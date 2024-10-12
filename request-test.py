import network
import requests 
from settings import Settings
import time
settings = Settings()



wlan = network.WLAN(network.STA_IF)
print("Connecting to " + settings.get("SSID") + ":")
wlan.active(True)
# Note SSID is case sensitive i.e. make sure it is gl24 not GL24
network.hostname(settings.get("HOSTNAME"))
print(settings.get("SSID"), settings.get("PASSWORD"))
wlan.connect(settings.get("SSID"), settings.get("PASSWORD"))
connectCount = 0
while not wlan.isconnected() and wlan.status() >= 0:
    time.sleep(1)
    connectCount+=1
    if connectCount>30:
        print(" wifi connect timed out")
    # Slow LED flash while connecting
    print(".", end="")
print('network config:', wlan.ipconfig('addr4'))


url="http://somerville.noip.me:37007/hello"
res = requests.get(url)
print(res.status_code)

