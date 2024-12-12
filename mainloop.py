import time
import machine
from machine import Pin, I2C
import json
import sys
import os

import freesansnum35
from settings import Settings
from ds3231 import DS3231
from statistic import Statistic
import bme280_float as bme280
from bg95m3 import Bg95m3
from ina219 import INA219
from logging import DEBUG
from iotwifi import IOTWifi
from writer import Writer
from ssd1306 import SSD1306_I2C
import pcf8575

#  Testing flags
quiet=False
skipLTE = False
skipWiFi = False

# Reboot daily to see if it improves reliability
doDailyReboot = True
# The waitForLTE flag is only set if an LTE connection fails
# and only applied after a reboot. This will 
# an attempt to do an LTE registration loop until it connects (for about 4 hours)
DOLTE_FILE_NAME="doLTEConnect.txt"
waitForLTE = False
lteConnectCount=0

try:
    os.stat(DOLTE_FILE_NAME)
    waitForLTE = True
except OSError:
    waitForLTE = False

settings = Settings()
CLIMATE_ID = 1
VEHICLE_ID = 3
LOCATION_ID = 4
IOT_ID = 7

OLED_WIDTH = 128
OLED_HEIGHT = 64


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
i2c = I2C(0, scl=Pin(13), sda=Pin(12),freq=200000)
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
    bme = bme280.BME280(i2c=i2c)
else:
    doClimate=False
if i2c.scan().count(0x40):
    ina = INA219(settings.get('SHUNT_OHMS'), i2c, log_level=DEBUG)
    ina.configure()
else:
    doVehicle=False
if i2c.scan().count(0x20) and i2c.scan().count(0x3c)  :
    # Set up ssd1306 (oled) and pcf8575 (IO Expander) objects
    oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c, addr=0x3c)
    pcf = pcf8575.PCF8575(i2c, 0x20)
else:
    hasOLED = False


not quiet and print("\nI2C flags - DS3231  RTC:",doDSRTC," Climate:",doClimate," Vehicle:",doVehicle," hasOLED:",hasOLED,"\n\n")


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
        global bme
        global statHumidity,statCelsius,statHPa

        # Get the climate data from the BME280 sensor and add to the accumulators
        t, p, h = bme.read_compensated_data()
        print("bmevalues:",t,p,h)
        statCelsius.addSample(t)
        statHumidity.addSample(h)
        statHPa.addSample(p/100)

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
    if doClimate and time.time() > 1704067201:
        # Only store data if we have a valid time set (> 2024)
        global statHumidity,statCelsius,statHPa
        iotData = {}
        iotData["celsius"] = round(statCelsius.average,2)
        iotData["hPa"] = round(statHPa.average,1)
        iotData["humidity"] = round(statHumidity.average,0)
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
    if doVehicle and time.time() > 1704067201:
        # Only store data if we have a valid time set (> 2024)
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
    global lteConnectCount,freeKB,usedKB
    if time.time() > 1704067201:
        # Only store data if we have a valid time set (> 2024)
        # get freespace
        stat = os.statvfs("/")
        size = stat[1] * stat[2]
        free = stat[0] * stat[3]
        used = size - free
        iotData = {}
        iotData["appID"] = IOT_ID
        iotData["sensorTimestamp"] = time.time()
        iotData["freeKB"] = free/1024 
        iotData["usedKB"] = used/1024 
        iotData["lteConnectCount"] = lteConnectCount
        lteConnectCount = 0
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
    if time.time() > 1704067201:
        # Only store data if we have a valid time set (> 2024)
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

def tryForLTE():
    global lteConnectCount
    not quiet and print(" Doing initial LTE registration as part of waitForLTE option")
    bg95m3 = Bg95m3(quiet)
    if not bg95m3.powerOn():
        bg95m3.powerOff()
        return False
    for connectCount in range(50):
        not quiet and print(" LTE Connect:",connectCount)
        lteConnectCount = connectCount
        if bg95m3.lteConnect():
            not quiet and print(" LTE Connect Successful")
            bg95m3.powerOff()
            time.sleep(1)
            return True
        time.sleep(1)
    bg95m3.powerOff()
    return False  

def doLTE(doGPS=True):
    if skipLTE:
        return False
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
            # Successful connect so remove the doLTEConnect file
            os.remove(DOLTE_FILE_NAME)
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
            with open(DOLTE_FILE_NAME, "w") as doLTE_file:
                doLTE_file.write("Yes")
            return False           

def doWifi():
    if skipWiFi:
        return False
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
    
def oledCenter(fontWidth,text): 
    charactersPerLine = OLED_WIDTH // fontWidth
    textCharacters = len(text)
    if textCharacters>=charactersPerLine:
        not quiet and print("oledCenter (16):",fontWidth,text,charactersPerLine,textCharacters,1)
        return 1
    else:
        col=int((charactersPerLine - textCharacters) * fontWidth//2) + 1
        not quiet and print("oledCenter:",fontWidth,text,charactersPerLine,textCharacters,col)
        return col
    
def oledDisplayValue(name,value):
    not quiet and print("oledDisplayValue:",name,value)
    oled.fill(0)
    Writer.set_textpos(oled, 0, 0)
    oled.text(name,  oledCenter(8,name), 0)
    oled.line(0, 15, oled.width - 1, 15, 1)
    # Use writer to write using the larger font
    wri = Writer(oled, freesansnum35, verbose=False)
    # Will base the centering on being able to fit 5 large characters on the line
    wri = Writer(oled, freesansnum35, verbose=False)
    Writer.set_textpos(oled, 25, oledCenter(15,str(value)))
    wri.printstring(str(value))
    oled.show()
    time.sleep(5)
    oled.fill(0)
    oled.show()
    
def showOLEDPower():
    not quiet and print("showOLEDPower")
    # get the current amps,and voltage and show on the oled
    if doVehicle:
        if statAmps.sampleCount >0:
            amps = round(statAmps.lastValue / 1000,3)
            if amps >0:
                if amps<1:
                    oledDisplayValue("Amps",round(amps,2))
                else:
                    oledDisplayValue("Amps",round(amps,1))
        else:
            oledDisplayValue("No Amp Samples",0)
        if statVolts.sampleCount >0:
            oledDisplayValue("Volts",round(statVolts.lastValue,2))
        else:
            oledDisplayValue("No Volt Samples",0)
        if statVolts.sampleCount >0 and statAmps.sampleCount >0:
            watts = (statAmps.lastValue / 1000) * statVolts.lastValue
            oledDisplayValue("Watts",round(watts ,1))
    else:
        oledDisplayValue("No Power Data",0)

def showOLEDClimate():
    not quiet and print("showOLEDClimate")
    # get the current amps,and voltage and show on the oled
    if doClimate:
        if statCelsius.sampleCount > 0:
            fahrenheit= round((statCelsius.lastValue * 1.8) + 32,1)
            oledDisplayValue("Fahrenheit",fahrenheit)
        else:
            oledDisplayValue("No Temp. Samples",0)
        if statHumidity.sampleCount >0:
            oledDisplayValue("Humidity",round(statHumidity.lastValue,0))
        else:
            oledDisplayValue("No Humidity Samples",0)
    else:
        oledDisplayValue("No Climate Data",0)



not quiet and print("*** First LTE Send ",time.localtime())
if doDSRTC:
    # for testing and only if the i2c based RTC is available
    # otherwise the time will be bad.
    getVehicle()
    storeVehicle()
getVehicle()
for x in range(2):
    ledFlash()
if waitForLTE:
    tryForLTE()

# Connecting to LTE but and get GPS and clock update
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
    if hasOLED:
        try:
            # Set the 2 i/o pins to check for button pushes to be high
            pcf.pin(0,1)
            if pcf.pin(0) == 0:
                # Show the current power usage on the display
                showOLEDPower()
            pcf.pin(1,1)
            if pcf.pin(1) == 0:
                # show the current climate on the display
                showOLEDClimate()
        except Exception as e:
                print("\npcfException")
                f=open('pcfexception.txt', 'w')  
                f.write(str(time.localtime()) + "\n")
                sys.print_exception(e,f)
                f.close()
                # Reload pcf device
                pcf = pcf8575.PCF8575(i2c, 0x20)
    # Check it time for daily reboot and time seems to be set
    if doDailyReboot and time.time() > 1704067201:
        # Check if it is 2:20AM (eastern time)
        ltyear,ltmonth,ltmday,lthour,ltminute,ltsecond,ltweekday,ltyearday = time.localtime()
        if lthour == 6 and ltminute==20:
            not quiet and print("*** Reboot time",time.localtime())
            f=open('reboot.txt', 'a')  
            f.write(str(time.localtime()) )
            f.close()
            machine.reset()
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


    time.sleep(0.5)
