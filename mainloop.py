import time
import machine
import json
import sys
import os

from settings import Settings
from ds3231 import DS3231
from statistic import Statistic
from  bme688 import BME680_I2C
from bg95m3 import Bg95m3
from ina219 import INA219
from logging import DEBUG

settings = Settings()
SHUNT_OHMS = 0.0015
CLIMATE_ID = 1
VEHICLE_ID = 3
LOCATION_ID = 3
IOT_ID = 7

# Create I2c interface objects
i2c = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)
ds = DS3231(i2c)
bme688 = BME680_I2C(i2c,address=0x76)
ina = INA219(settings.get('SHUNT_OHMS'), i2c, log_level=DEBUG)
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
quiet=False


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
    iotData["appID"] = CLIMATE_ID
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
    iotData["houseVolts"] = round(statVolts.average,2)
    iotData["houseAmps"]= round((statAmps.average/1000),3)
    iotData["sensorTimestamp"] = time.time()
    iotData["appID"] = VEHICLE_ID
    print(iotData)
    file = "data/" + str(time.time()) + getUniqueMs() + ".json"
    print(file)
    with open(file, "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))
    statVolts.reset()
    statAmps.reset()

def doLTE():
    sendSecondStart = time.time()
    # Do LTE and GPS operations if we can connect
    bg95m3 = Bg95m3(quiet)
    filesSent=0
    if not bg95m3.powerOn():
        # No successful LTE modem startup, give up until next time
        bg95m3.powerOff()
    else:
        for fileName in os.listdir("data"):
            with open("data/" + fileName, "r") as iotDataFile:
                not quiet and print("Sending ",fileName," to iotCache...")
                iotData = json.load(iotDataFile)
                iotData["user"] = settings.get("USER")
                iotData["deviceID"] = settings.get("DEVICEID") 
                request = 'http://somerville.noip.me:37007/write?iotData=' + json.dumps(iotData).replace("\'","\"").replace(" ","")
                not quiet and print("request:",request)
                result=bg95m3.httpGet(request)
                if result:
                    filesSent+=1
                    not quiet and print("remove:",fileName)
                    # os.remove("data/" + fileName)
                else:
                    break
                # Only process one file per event loop
                break
        # Get GPS info
        gps = bg95m3.getLocation()
        not quiet and print("gps:",gps)
        if gps:
            nop

        # Update IOT info
        rssi = bg95m3.getRSSI()
        not quiet and print("rssi:",rssi)
        iotData = {}
        iotData["user"] = settings.get("USER")
        iotData["deviceID"] = settings.get("DEVICEID") 
        iotData["appID"] = IOT_ID
        iotData["sensorTimestamp"] = time.time()
        iotData["RSSI"] = rssi
        if gps:
            iotData["gpsSeconds"] = gps["duration"]
        iotData["sendSeconds"] = time.time() - sendSecondStart
        iotData["uptimeSeconds"] = time.time() - upTimeStart
        iotData["fileSent"] = filesSent
        request = 'http://somerville.noip.me:37007/write?iotData=' + json.dumps(iotData).replace("\'","\"").replace(" ","")
        not quiet and print("request:",request)
        result=bg95m3.httpGet(request)
        time.sleep(5)

        # print("Power off")
        bg95m3.powerOff()
        # del bg95m3

doLTE()
sys.exit(0)

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
        # doLTE()


    time.sleep(event_loop_seconds)
