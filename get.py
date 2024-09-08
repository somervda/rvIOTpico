"""
Example code for performing GET request to a server with using HTTP.

Example Configuration
---------------------
Create a config.json file in the root directory of the PicoLTE device.
config.json file must include the following parameters for this example:

config.json
{
    "https":{
        "server":"[HTTP_SERVER]",
        "username":"[YOUR_HTTP_USERNAME]",
        "password":"[YOUR_HTTP_PASSWORD]"
    },
}
"""

import time
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

import machine


 




if False:
    picoLTE = PicoLTE()
    picoLTE.network.register_network()
    picoLTE.http.set_context_id()
    picoLTE.network.get_pdp_ready()

    picoLTE.http.set_server_url("http://somerville.noip.me:37007/status?user=david")
    debug.info("Sending a GET request.")

    result = picoLTE.http.get()
    debug.info(result)

    # Read the response after 1 seconds.
    time.sleep(1)
    result = picoLTE.http.read_response()
    debug.info(result)


    if result["status"] == Status.SUCCESS:
        debug.info("Get request succeeded.")

    # see https://sixfab.com/wp-content/uploads/2023/05/Quectel_BG95BG77BG600L_Series_AT_Commands_Manual_V2.0.pdf
    command = "AT+CSQ"
    result = picoLTE.atcom.send_at_comm(command)
    rssi= result['response'][0].split(":")[1].split(',')[0]
    print(rssi)
    print("rssi:",(int(rssi.strip())*2)-109,"db")

    # Power off modem after request
    picoLTE.base.power_off()



if False:
    picoLTE = PicoLTE()
    debug.info("Get GPS")
    # First go to GNSS prior mode and turn on GPS.
    picoLTE.gps.set_priority(0)
    time.sleep(3)
    picoLTE.gps.turn_on()
    debug.info("Trying to fix GPS...")

    for x in range(0, 60):
        result = picoLTE.gps.get_location()
        debug.info(x,result)

        if result["status"] == Status.SUCCESS:
            debug.debug("GPS Fixed. Getting location data...")

            loc = result.get("value")
            debug.info("Lat-Lon:", loc)
            loc_message = ",".join(word for word in loc)

            fix = True
            break
        time.sleep(5)  # 60*5 = 3 minutes timeout for GPS fix.



# qwiic interface
print('Scan i2c bus...')
i2c = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))

  for device in devices:  
    print("Decimal address: ",device," | Hexa address: ",hex(device))

if True:
    # code to read adc value
    # from ads1x15 import ADS1115
    # adc = ADS1115(i2c, address=72, gain=1)
    # value = adc.read(0, 0)
    # print(value)

    from ina219 import INA219
    from logging import DEBUG

    # change this to match 50amp 75mv shunt resistor
    # in parallel with onboard ina219 0.1 ohm shunt (Makes little difference)
    # will do some tests latter to do any adjustments
    # Best resolution at 12 bits will be around 0.06A
    SHUNT_OHMS = 0.0015

    ina = INA219(SHUNT_OHMS, i2c, log_level=DEBUG)
    ina.configure()
    print("Bus Voltage: %.3f V" % ina.voltage())
    print("Current: %.3f mA" % ina.current())
    print("Power: %.3f mW" % ina.power())

# Get climate data using adafuit bme688
#  See https://randomnerdtutorials.com/micropython-bme680-esp32-esp8266/
# I used this version of the library https://github.com/CRCibernetica/bme688-i2c-micropython 
# Common products with high VOC https://apps.ecology.wa.gov/cleanupsearch/document/69000 
if False:
    from  bme688 import BME680_I2C
    sensor = BME680_I2C(i2c,address=0x76)

    while True:
        gas = sensor.gas
        temperature = sensor.temperature
        humidity = sensor.humidity
        pressure = sensor.pressure
        print(f'Temp: {temperature:.1f}C,  RH: {humidity:.1f}%,  Pressure: {pressure:.1f}kPa,  Gas: {gas:.0f}')
        time.sleep(5)


#  RTC
# https://github.com/pangopi/micropython-DS3231-AT24C32
# Sets the RTC based on current pico time
if True:
    from ds3231 import DS3231
    ds = DS3231(i2c)

    print("1. RTC:",ds.datetime())
    localtime=list(time.localtime())
    print("2. localtime:",localtime)
    year = localtime[0]
    month = localtime[1]
    mday = localtime[2]
    hour = localtime[3]+4
    minute = localtime[4]
    second = localtime[5]
    weekday = localtime[6]

    if hour>23:
        print("Error: Cant set gmt time, try again tomorrow morning:",localtime)
    else:
        gmt=(year, month, mday, hour, minute, second,weekday)
        print("3. gmt:",gmt)
        # Set realtime clock to gmt
        # Note setting time tuple is different order from getting time tuple
        ds.datetime(gmt)
    print("4 new RTC:",ds.datetime())