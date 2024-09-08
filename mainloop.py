import time
import machine
import json

from settings import Settings
from ds3231 import DS3231
from statistic import Statistic
from  bme688 import BME680_I2C
from ina219 import INA219
from logging import DEBUG

settings = Settings()
# Create I2c interface objects
i2c = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)
ds = DS3231(i2c)
bme688 = BME680_I2C(i2c,address=0x76)
SHUNT_OHMS = 0.0015
ina = INA219(SHUNT_OHMS, i2c, log_level=DEBUG)
ina.configure()

# Set current pico RTC time to metric time from RTC module
rtc = machine.RTC()
rtc.datetime(ds.datetime())
upTimeStart = time.time()
# Initialize last times data was collected and sent (Start of last minute and hour)
lastSample = time.time() - (time.time() % settings.get('SAMPLE_SECONDS') )
lastSend = time.time() - (time.time() % settings.get('SEND_SECONDS') )


event_loop_seconds = settings.get('EVENT_LOOP_SECONDS')
uniqueMs = 0


statCelsius = Statistic("Celsius")
statHPa = Statistic("hPa")
statHumidity = Statistic("Humidity")
statVOC = Statistic("VOC")
statVolts = Statistic("houseBattery")
statAmps = Statistic("houseAmps")


def getUniqueMs():
    global uniqueMs
    uniqueMs+=1
    if uniqueMs > 999:
        uniqueMs =0
    return "{:03d}".format(uniqueMs)    


def getClimate():
    global bme688
    global statHumidity,statVOC,statCelsius,statHPa
    # Get the climate data from the BME688 sensor and add to the accumulators
    statCelsius.addSample(bme688.temperature)
    statHumidity.addSample(bme688.humidity)
    statHPa.addSample(bme688.pressure)
    time.sleep(2)
    statVOC.addSample(bme688.gas)

def getVehicle():
    global statVolts,statAmps
    global ina
    # Get the power data from the INA219 sensor and add to the accumulators
    statVolts.addSample(ina.voltage())
    statAmps.addSample(ina.current())


def storeClimate():
    # Get averages for any climate statistics
    # store them in a date stamped json file 
    # for sending to the IOT server 
    global statHumidity,statVOC,statCelsius,statHPa
    iotData = {}
    iotData["celsius"] = round(statCelsius.average,2)
    iotData["hPa"] = round(statHPa.average,1)
    iotData["humidity"] = round(statHumidity.average,0)
    iotData["voc"] = round(statVOC.average,0)
    iotData["sensorTimestamp"] = time.time()
    print(iotData)
    file = "data/" + str(time.time()) + getUniqueMs() + ".json"
    print(file)
    with open(file, "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))
    statCelsius.reset()
    statHPa.reset()
    statHumidity.reset()
    statVOC.reset()

def storeVehicle():
    # Get averages for any vehicle statistics
    # store them in a date stamped json file 
    # for sending to the IOT server 
    global statVolts,statAmps
    iotData = {}
    iotData["houseBattery"] = round(statVolts.average,2)
    iotData["houseAmps"]= round((statAmps.average/1000),3)
    iotData["sensorTimestamp"] = time.time()
    print(iotData)
    file = "data/" + str(time.time()) + getUniqueMs() + ".json"
    print(file)
    with open(file, "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))
    statVolts.reset()
    statAmps.reset()



# Main event loop
while True:
    # Is it sample time
    if (time.time() - lastSample >= settings.get('SAMPLE_SECONDS')):
        lastSample = time.time() - (time.time() % settings.get('SAMPLE_SECONDS') )
        print("*** Do Sample:",time.localtime())
        getClimate()
        getVehicle()
    # Is it LTE xmit time
    if (time.time() - lastSend >= settings.get('SEND_SECONDS')):
        lastSend = time.time() - (time.time() % settings.get('SEND_SECONDS') ) 
        print("*** Do Send",time.localtime())
        storeClimate()
        storeVehicle()


    time.sleep(event_loop_seconds)
