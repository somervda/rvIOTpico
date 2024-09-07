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

# acTemp = Accumulator()
# acTemp.addSample(74)
# time.sleep(4)
# acTemp.addSample(75)
# time.sleep(6)
# acTemp.addSample(79)
# print(acTemp.average,acTemp.duration)
# acTemp.reset()
# print(acTemp.average,acTemp.duration)

stat_Temp = Statistic("Temperature")
stat_hPa = Statistic("hPa")
stat_Humidity = Statistic("Humidity")
stat_VOC = Statistic("VOC")

def getClimate():
    # Get the climate data from the BME688 sensor and add to the accumulators
    stat_VOC.addSample(bme688.gas)
    stat_Temp.addSample(bme688.temperature)
    stat_Humidity.addSample(bme688.humidity)
    stat_hPa.addSample(bme688.pressure)



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
        lastHour = currentHour

    time.sleep(event_loop_seconds)
