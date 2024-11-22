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
from iotwifi import IOTWifi



quiet=False

settings = Settings()
CLIMATE_ID = 1
VEHICLE_ID = 3
LOCATION_ID = 4
IOT_ID = 7


doClimate=True
doVehicle=True
doDSRTC=True
hasOLED=True


led = machine.Pin("LED", machine.Pin.OUT)
def ledFlash():
    led.on()
    time.sleep(1)
    led.off()
    time.sleep(0.5)

ledFlash()

userButton = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Create I2c interface objects
# Circuit python lib https://github.com/robert-hh/INA219
i2c = machine.I2C(0, scl=machine.Pin(13), sda=machine.Pin(12), freq=100000)
for device in i2c.scan():
    not quiet and print("I2C hexadecimal address: ", hex(device))

# Check if DS3231, INA219 and BME688 are present
#  on the i2c bus
print(i2c.scan())
if i2c.scan().count(0x68):
    ds = DS3231(i2c)
else:
    doDSRTC=False
if i2c.scan().count(0x76):
    bme688 = BME680_I2C(i2c,address=0x76)
else:
    doClimate=False
if i2c.scan().count(0x40):
    ina = INA219(settings.get('SHUNT_OHMS'), i2c, log_level=DEBUG)
    ina.configure()
else:
    doVehicle=False
if i2c.scan().count(0x20) and i2c.scan().count(0x3C) :
    # Set up ssd1306 (oled) and pcf8575 (IO Expander) objects
    NotImplemented
else:
    hasOLED = False

not quiet and print("I2C flags - DS3231  RTC:",doDSRTC," Climate:",doClimate," Vehicle:",doVehicle," hasOLED:",hasOLED)

# print("Voltage, current : ",ina.voltage(),ina.current())
# sys.exit(0)

# Make a wifi object incase I need to try and send over wifi if LTE not connecting
wifi = IOTWifi(quiet)


# Set current pico RTC time to time from DS3231 RTC module
rtc = machine.RTC()
not quiet and print("pico RTC:",rtc.datetime())
if doDSRTC:
    not quiet and print("DS3231 RTC:",ds.datetime())
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
    if doClimate:
        global bme688
        global statHumidity,statVOC,statCelsius,statHPa
        # Get the climate data from the BME688 sensor and add to the accumulators
        statCelsius.addSample(bme688.temperature)
        statHumidity.addSample(bme688.humidity)
        statHPa.addSample(bme688.pressure)
        time.sleep(0.1)
        statVOC.addSample(bme688.gas)

def getVehicle():
    if doVehicle:
        global statVolts,statAmps
        global ina
        # Get the power data from the INA219 sensor and add to the accumulators
        statVolts.addSample(ina.voltage())
        statAmps.addSample(ina.current())


def storeClimate():
    # Get averages for any climate statistics
    # store them in a date stamped json file 
    # for sending to the IOT server 
    if doClimate:
        global statHumidity,statVOC,statCelsius,statHPa
        iotData = {}
        iotData["celsius"] = round(statCelsius.average,2)
        iotData["hPa"] = round(statHPa.average,1)
        iotData["humidity"] = round(statHumidity.average,0)
        if time.time() - upTimeStart > 10800:
            # Only start recording VOC info after the probe has been running for 3 hours
            # this helps reduce the impact of the BMR688 warm up time
            iotData["voc"] = round(statVOC.average,0)
        iotData["sensorTimestamp"] = time.time()
        iotData["appID"] = CLIMATE_ID
        file = "data/" + str(time.time()) + getUniqueMs() + ".json"
        not quiet and print("Saving... ",file,iotData)
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
    if doVehicle:
        global statVolts,statAmps
        iotData = {}
        iotData["houseVolts"] = round(statVolts.average,2)
        iotData["houseAmps"]= round((statAmps.average/1000),3)
        iotData["sensorTimestamp"] = time.time()
        iotData["appID"] = VEHICLE_ID
        file = "data/" + str(time.time()) + getUniqueMs() + ".json"
        not quiet and print("Saving... ",file,iotData)
        with open(file, "w") as sensor_data_file:
                sensor_data_file.write(json.dumps(iotData))
        statVolts.reset()
        statAmps.reset()

def storeIOT(gpsSeconds,sendSeconds,filesSent,rssi,wifiFilesSent,ssidIndex=-1):
    iotData = {}
    iotData["appID"] = IOT_ID
    iotData["sensorTimestamp"] = time.time()
    if rssi:
        iotData["RSSI"] = rssi 
    if gpsSeconds:
        iotData["gpsSeconds"] = gpsSeconds
    iotData["sendSeconds"] = sendSeconds
    iotData["uptimeSeconds"] = time.time() - upTimeStart
    if filesSent:
        iotData["filesSent"] = filesSent
    if wifiFilesSent:
        iotData["wififilesSent"] = wifiFilesSent
    iotData["ssid"] = ssidIndex
    file = "data/" + str(time.time()) + getUniqueMs() + ".json"
    not quiet and print("Saving... ",file,iotData)
    with open(file, "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))

def storeGPS(gpsData):
    iotData = {}
    iotData["appID"] = LOCATION_ID
    iotData["sensorTimestamp"] = time.time()
    iotData["latitude"] = gpsData["latitude"] 
    iotData["longitude"] = gpsData["longitude"] 
    file = "data/" + str(time.time()) + getUniqueMs() + ".json"
    not quiet and print("Saving... ",file,iotData)
    with open(file, "w") as sensor_data_file:
            sensor_data_file.write(json.dumps(iotData))

def checkGPSTime(gpsData):
    global ds,rtc
    # The time received from the GPS is the most accurate
    # Check to see if the pico RTC is out of sync (By more than a minute), if it is
    # then update the pico RTC and the DS3231 RTC 
    picoRTC = rtc.datetime()
    if gpsData["year"] != picoRTC[0] or gpsData["month"] != picoRTC[1] \
        or gpsData["day"] != picoRTC[2] or gpsData["hour"] != picoRTC[4] \
        or gpsData["minute"] != picoRTC[5]:
        # Update the RTCs
        gmtDS=(gpsData["year"], gpsData["month"], gpsData["day"], gpsData["hour"], gpsData["minute"], gpsData["second"])
        not quiet and print("RTC out of sync with GPS:",picoRTC,gmtDS)
        if doDSRTC:
            ds.datetime(gmtDS)
        gmtPico=(gpsData["year"], gpsData["month"], gpsData["day"],0, gpsData["hour"], gpsData["minute"], gpsData["second"],0)
        rtc.datetime(gmtPico)
        not quiet and print("RTCs updated")




def doLTE(doGPS=True):
    sendSecondStart = time.time()
    # Do LTE and GPS operations if we can connect
    bg95m3 = Bg95m3(quiet)
    filesSent=0
    if not bg95m3.powerOn():
        # No successful LTE modem startup, give up until next time
        bg95m3.powerOff()
        return False
    else:
        rssi=None
        # GPS processing 
        gpsStartTime = time.time()
        if doGPS:
            # This is stored  as a iotData file and sent in the next part of the code
            gpsData = bg95m3.getLocation()
            not quiet and print("gpsData:",gpsData)
            if gpsData:
                storeGPS(gpsData)
                checkGPSTime(gpsData)
        gpsSeconds = time.time() - gpsStartTime

        # Send any available iotData files
        if bg95m3.lteConnect():
            fullSendSuccess=False
            for fileName in os.listdir("data"):
                with open("data/" + fileName, "r") as iotDataFile:
                    not quiet and print("Sending ",fileName," to iotCache over LTE...")
                    iotData = json.load(iotDataFile)
                    iotData["user"] = settings.get("USER")
                    iotData["deviceID"] = settings.get("DEVICEID") 
                    url = 'http://' +  settings.get("LOGGERHOST") + ':' +  str(settings.get("LOGGERPORT")) + '/write?iotData=' + json.dumps(iotData).replace("\'","\"").replace(" ","")
                    not quiet and print("url:",url)
                    result=bg95m3.httpGet(url)
                    if result:
                        filesSent+=1
                        not quiet and print("remove:",fileName)
                        os.remove("data/" + fileName)
                        fullSendSuccess=True
                    else:
                        # Stop trying to send if a send fails
                        not quiet and print("doLTE file send failed:",fileName)
                        fullSendSuccess=False
                        break
                    # Only process one file per event loop
                    # break
                    time.sleep(1)
            rssi = bg95m3.getRSSI()
            not quiet and print("rssi:",rssi)

            # Store IOT info 
            # This is stored as a iotData file 
            storeIOT(gpsSeconds,time.time() - sendSecondStart,filesSent,rssi,None)
            # If all files had been sent successfully , try to also send the IOT info we just created
            # This is optional send so is not counted against successful files sends, otherwise IOT application
            # data is sent next send cycle
            if fullSendSuccess:
                for fileName in os.listdir("data"):
                    with open("data/" + fileName, "r") as iotDataFile:
                        not quiet and print("Sending optional ",fileName," to iotCache over LTE...")
                        iotData = json.load(iotDataFile)
                        iotData["user"] = settings.get("USER")
                        iotData["deviceID"] = settings.get("DEVICEID") 
                        if iotData["filesSent"]:
                            iotData["filesSent"] = iotData["filesSent"] + 1
                        url = 'http://' +  settings.get("LOGGERHOST") + ':' +  str(settings.get("LOGGERPORT")) + '/write?iotData=' + json.dumps(iotData).replace("\'","\"").replace(" ","")
                        not quiet and print("url:",url)
                        result=bg95m3.httpGet(url)
                        if result:
                            not quiet and print("remove:",fileName)
                            os.remove("data/" + fileName)
                        # Only send one file
                        break
            # Clean up
            bg95m3.powerOff()
            return fullSendSuccess
        else:
            # lteConnect failed
            bg95m3.powerOff()
            return False           

def doWifi():
    sendSecondStart = time.time()
    wifiFilesSent=0
    gpsSeconds=None
    ssidIndex = wifi.connect()
    if ssidIndex != None:
        # Send any available iotData files
        time.sleep(2)
        fullSendSuccess=False
        for fileName in os.listdir("data"):
            with open("data/" + fileName, "r") as iotDataFile:
                not quiet and print("Sending ",fileName," to iotCache over wifi...")
                iotData = json.load(iotDataFile)
                iotData["user"] = settings.get("USER")
                iotData["deviceID"] = settings.get("DEVICEID") 
                url = 'http://' + settings.get("LOGGERHOST") + ':' + str(settings.get("LOGGERPORT")) + '/write?iotData=' + json.dumps(iotData).replace("\'","\"").replace(" ","")
                not quiet and print("url:",url)
                result=wifi.send(url)
                if result:
                    wifiFilesSent+=1
                    not quiet and print("remove:",fileName)
                    os.remove("data/" + fileName)
                    fullSendSuccess=True
                else:
                    # Stop trying to send if a send fails
                    fullSendSuccess=False
                    break
                # Only process one file per event loop
                # break
                time.sleep(1)
        wifi.powerOff()
        storeIOT(gpsSeconds,time.time() - sendSecondStart,None,None,wifiFilesSent,ssidIndex)
        return fullSendSuccess
    else:
        return False

not quiet and print("*** First LTE Send ",time.localtime())
if doDSRTC:
    # for testing and only if the i2c based RTC is available
    # otherwise the time will be bad.
    getVehicle()
    storeVehicle()
getVehicle()
sys.exit(0)
for x in range(2):
    ledFlash()
doLTE(doGPS=True)
# Always go through a wifi cycle on startup
# even if it fails it will shutdown the wifi components
# at the end and save power
doWifi()

# sys.exit(0)

# Main event loop
while True:
    # Exit loop if userButton on Sixfab board is pressed
    if userButton.value() == 0:
        print("Exit mainLoop")
        for x in range(4):
            ledFlash()
        break
    # If the led display module is attached then check if one
    # of the 2 status buttons has been pressed and display the 
    # battery or climate data

    # Is it sample time
    if (time.time() - lastSample >= settings.get('SAMPLE_SECONDS')):
        lastSample = time.time() - (time.time() % settings.get('SAMPLE_SECONDS') )
        not quiet and print("*** Do Sample:",time.localtime())
        ledFlash()
        getClimate()
        getVehicle()
        ledFlash()
    # Is it LTE xmit time
    if (time.time() - lastSend >= settings.get('SEND_SECONDS')):
        lastSend = time.time() - (time.time() % settings.get('SEND_SECONDS') ) 
        not quiet and print("*** Do Send",time.localtime())
        for x in range(2):
            ledFlash()
        storeClimate()
        storeVehicle()
        LTEsuccess = doLTE(doGPS=True)
        not quiet and print("lteSuccess:",LTEsuccess)
        if not LTEsuccess:
            not quiet and print("doWIFI")
            doWifi()


    time.sleep(event_loop_seconds)
