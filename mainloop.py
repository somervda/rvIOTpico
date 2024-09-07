import time
import machine

from settings import Settings
from ds3231 import DS3231
from statistic import Statistic
from  bme688 import BME680_I2C

# Create I2c interface objects
i2c = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)
ds = DS3231(i2c)
bme688 = BME680_I2C(i2c,address=0x76)

# Set current pico RTC time to metric time from RTC module
rtc = machine.RTC()
rtc.datetime(ds.datetime())
# Initialize last minute/hour values
lastHour = time.localtime()[3]
lastMinute = time.localtime()[4]


settings = Settings()
event_loop_seconds = settings.get('EVENT_LOOP_SECONDS')
uniqueMs = 0


statCelsius = Statistic("Celsius")
statHPa = Statistic("hPa")
statHumidity = Statistic("Humidity")
statVOC = Statistic("VOC")

def getUniqueMs():
    global uniqueMs
    uniqueMs+=1
    if uniqueMs > 999:
        uniqueMs =0
    return "{}".format(timestamp) + "{:03d}".format(uniqueMs)    

def getClimate():
    global statHumidity,statVOC,statCelsius,statHPa
    # Get the climate data from the BME688 sensor and add to the accumulators
    statVOC.addSample(bme688.gas)
    statCelsius.addSample(bme688.temperature)
    statHumidity.addSample(bme688.humidity)
    statHPa.addSample(bme688.pressure)

def storeClimate():
    # Get averages for any climate statistics
    # store them in a date stamped json file 
    # for sending to the IOT server 
    global statHumidity,statVOC,statCelsius,statHPa
    iotData = {}
    iotData["celsius"] = statCelsius.average
    iotData["hPa"] = statHPa.average
    iotData["humidity"] = statHumidity.average
    iotData["voc"] = statVOC.average
    iotData["sensorTimestamp"] = time.time()
    with open("data/" + str(time.time()) + getUniqueMs + ".json", "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))
    statCelsius.reset()
    statHPa.reset()
    statHumidity.reset()
    statVOC.reset()


# Main event loop
while True:
    print(time.localtime(),lastHour,lastMinute)
    currentHour = time.localtime()[3]
    currentMinute = time.localtime()[4]
    # Is it sample time
    if (lastMinute != currentMinute):
        print("Do Sample")
        getClimate()
        lastMinute = currentMinute
    # Is it LTE xmit time
    if (lastHour != currentHour):
        print("Do LTE")
        storeClimate()
        lastHour = currentHour

    time.sleep(event_loop_seconds)
