import network
import socket 
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


url="http://somerville.noip.me/hello"
_, _, fullhost, path = url.split('/', 3)
addr = socket.getaddrinfo(host, 37007)[0][-1]
s = socket.socket()
s.connect(addr)
s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
while True:
    data = s.recv(100)
    if data:
        print(str(data, 'utf8'), end='')
    else:
        break
s.close()

