import uasyncio as asyncio
from machine import Pin, SPI
from max6675 import Max6675
from microdot import Microdot, Response
import wifimgr

# Initialize thermocouple
cs = Pin(15, Pin.OUT)
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
sensor = Max6675(spi, cs)

# Initialize web server
app = Microdot()

# Asynchronous function to read temperature
async def read_temperature():
    return sensor.read()

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

# Route for serving the index page with the chart
@app.route('/')
async def index(request):
    try:
        with open('/data.txt', 'r') as f:
            data = f.read()
    except OSError:
        data = ""

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Temperature Data</title>
        <script src="https://code.highcharts.com/highcharts.js"></script>
    </head>
    <body>
        <div id="container" style="width:100%; height:400px;"></div>
        <script>
            const data = `{}`;
            const lines = data.trim().split('\\n');
            const seriesData = lines.map(line => parseFloat(line));

            Highcharts.chart('container', {
                title: { text: 'Temperature Data' },
                series: [{
                    name: 'Temperature',
                    data: seriesData
                }]
            });
        </script>
    </body>
    </html>
    """.format(data)

    return Response(body=html_content, content_type='text/html')

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
