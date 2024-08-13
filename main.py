import uasyncio as asyncio
from machine import Pin, SPI
from max6675 import Max6675
from microdot import Microdot, Response
import wifimgr
import random

# Initialize thermocouple
# Initialize the SPI interface
spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(18), mosi=None, miso=Pin(12))
# Initialize the chip select pin
cs_pin = Pin(5, Pin.OUT)

# Create an instance of the Max6675 class
temperature_sensor = Max6675(spi, cs_pin)

# Initialize web server
app = Microdot()


# Asynchronous function to generate mock temperature data
async def read_temperature():
    return temperature_sensor.read()
# async def read_temperature():
#     # Mock temperature data between 20 and 100 degrees Celsius

#     return round(random.uniform(20.0, 100.0), 2)


# Asynchronous function to write data to a file
async def write_to_file(data):
    with open('/data.txt', 'a') as f:
        f.write('{}\n'.format(data))


# Asynchronous task to log temperature periodically
async def temperature_logging_task():
    while True:
        temp = await read_temperature()
        await write_to_file(temp)
        await asyncio.sleep(1)  # Adjust the interval as needed


async def get_coffee_html():
    with open('html/coffee_log.html', 'r') as html_file:
        coffee_html = html_file.read()
    return coffee_html


# Route for serving the index page with the chart
@app.route('/')
async def index(request):
    coffee_html = await get_coffee_html()
    headers = {'Content-Type': 'text/html'}
    return Response(body=coffee_html, headers=headers)


@app.route('/data')
async def data(request):
    temp = await read_temperature()
    headers = {'Content-Type': 'application/json'}
    return Response(body={'data': [temp]}, headers=headers)


# Main function to handle WiFi setup, server, and logging
async def main():
    # Initialize WiFi Manager
    wlan = wifimgr.get_connection()

    if wlan is not None:
        # If connected, start the web server and logging task
        print("Connected to WiFi:", wlan.ifconfig())
        asyncio.create_task(app.start_server(port=80))
        asyncio.create_task(temperature_logging_task())
    else:
        # If not connected, WiFiManager will already have started its configuration AP
        print("Could not connect to WiFi, started configuration AP")

    # Main loop to keep the program running
    while True:
        await asyncio.sleep(1)


# Run the main function in an asyncio loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program interrupted")
