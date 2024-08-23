import os

import uasyncio as asyncio
from machine import Pin, SPI
from max6675 import Max6675
from microdot.microdot import Microdot, Response, send_file
import wifimgr
import time
from microdot.websocket import WebSocket, with_websocket
import ujson as json
from finalize_log import add_events_to_log


# Initialize thermocouple
spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(18), mosi=None, miso=Pin(12))
cs_pin = Pin(5, Pin.OUT)
temperature_sensor = Max6675(spi, cs_pin)
connected_clients = []  # List to keep track of connected WebSocket clients
events = {}

app = Microdot()
log_file_path = 'roast_log.txt'
# Assume roast_start_time is globally defined and updated elsewhere in your program
roast_start_time = 0  # Set this appropriately
is_roast_active = False  # This should be set based on whether the roast is active or not
charge_started = False
charge_start_time = 0


async def read_temperature():
    celsius = temperature_sensor.read()
    fahrenheit = (celsius * 9 / 5) + 32
    return fahrenheit


async def write_to_file(data):
    with open(log_file_path, 'a') as f:
        f.write(f'{data}\n')


async def temperature_logging_task():
    global is_roast_active, charge_started, roast_start_time
    while True:
        if is_roast_active:
            # Calculate total elapsed time
            elapsed_time = time.time() - roast_start_time
            elapsed_minutes = elapsed_time // 60
            elapsed_seconds = elapsed_time % 60
            elapsed_str = f"{int(elapsed_minutes):02d}:{int(elapsed_seconds):02d}"
            temp = await read_temperature()
            if charge_started:
                # Calculate total elapsed time
                elapsed_charge_time = time.time() - charge_start_time
                elapsed_charge_minutes = elapsed_charge_time // 60
                elapsed_charge_seconds = elapsed_charge_time % 60
                elapsed_charge_str = f"{int(elapsed_charge_minutes):02d}:{int(elapsed_charge_seconds):02d}"
            else:
                elapsed_charge_str = f"{int(00):02d}:{int(00):02d}"

            log_line = "\t".join([elapsed_str, elapsed_charge_str, "0", f"{temp}", ""])
            await write_to_file(log_line)
        await asyncio.sleep(1)


# Define a WebSocket route using the with_websocket decorator
@app.route('/ws')
@with_websocket
async def websocket(request, ws: WebSocket):
    while True:
        message = await ws.receive()
        if message is None:
            break
        print('Received via WebSocket:', message)
        await ws.send('Echo: ' + message)


async def get_coffee_html():
    with open('html/coffee_log.html', 'r') as html_file:
        coffee_html = html_file.read()
    return coffee_html


@app.route('/')
async def index(request):
    coffee_html = await get_coffee_html()
    headers = {'Content-Type': 'text/html'}
    return Response(body=coffee_html, headers=headers)


async def start_roast():
    global is_roast_active, roast_start_time
    if not is_roast_active:
        roast_start_time = time.time()
        is_roast_active = True


async def stop_roast():
    global is_roast_active, roast_start_time, charge_started, charge_start_time, events
    if is_roast_active:
        is_roast_active = False
        roast_start_time = 0
        charge_started = False
        charge_start_time = 0
        add_events_to_log(events, log_file_path)


@app.route('/ws/add_event')
@with_websocket
async def add_event_websocket(request, ws):
    global is_roast_active, events, charge_started, charge_start_time
    try:
        while True:
            # Receive event name from the client
            message = await ws.receive()
            if message is None:
                break
            # Parse the event name from the received message
            event_data = json.loads(message)
            event_name = event_data.get('event')

            # Calculate total elapsed time
            elapsed_time = time.time() - roast_start_time
            elapsed_minutes = elapsed_time // 60
            elapsed_seconds = elapsed_time % 60
            elapsed_str = f"{int(elapsed_minutes):02d}:{int(elapsed_seconds):02d}"

            if event_name == 'START':
                await start_roast()
                print(f"Roast Started!")
            elif event_name == 'STOP':
                await stop_roast()
                print(f"Roast Stopped!")
            elif is_roast_active:
                # Add the event to the global dictionary
                events[elapsed_str] = event_name
                print(f"Event added: {elapsed_str} -> {event_name}")
                if event_name == 'CHARGE':
                    charge_start_time = time.time()
                    charge_started = True
            else:
                print(f"{event_name} skipped no roast active")

            # Optionally, send a confirmation back to the client
            confirmation = json.dumps({'status': 'success', 'elapsed_time': elapsed_str, 'event': event_name})
            await ws.send(confirmation)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws.close()

@app.route('/ws/data')
@with_websocket
async def data_websocket(request, ws: WebSocket):
    connected_clients.append(ws)
    try:
        while True:
            # Read temperature and calculate elapsed time
            temp = await read_temperature()
            elapsed_time = time.time() - roast_start_time if is_roast_active else 0

            # Prepare the data as a JSON string
            data = {'data': [temp, elapsed_time]}
            json_data = json.dumps(data)  # Serialize the dictionary to a JSON string

            # Send the JSON string back to all connected clients
            for client in connected_clients:
                try:
                    await client.send(json_data)
                except OSError as e:
                    print(f"Error sending to client: {e}")
                    connected_clients.remove(client)  # Remove client if sending fails

            # Wait for 1 second before sending the next update
            await asyncio.sleep(1)

    except OSError as e:
        if e.errno == 104:  # ECONNRESET
            print("Client disconnected, connection reset by peer")
        else:
            print(f"WebSocket error: {e}")
    finally:
        # Ensure the WebSocket is closed cleanly and remove it from the list
        await ws.close()
        connected_clients.remove(ws)


@app.route('/download')
async def download_data(request):
    try:
        headers = {'Content-Type': 'text/csv'}

        return send_file(log_file_path, content_type=headers['Content-Type'], )
    except Exception as e:
        print(e)
        headers = {'Content-Type': 'text/html'}
        return Response(body="File not Found", headers=headers)


async def main():
    wlan = wifimgr.get_connection()
    if wlan is not None:
        print("Connected to WiFi:", wlan.ifconfig())
        asyncio.create_task(app.start_server(port=80))
        asyncio.create_task(temperature_logging_task())
    else:
        print("Could not connect to WiFi, started configuration AP")

    while True:
        await asyncio.sleep(1)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program interrupted")
