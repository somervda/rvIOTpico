from bg95m3 import Bg95m3
import time

print("Init object")
bg95m3 = Bg95m3()
# result=bg95m3.send("http://somerville.noip.me:37007/status?user=david")
# print("send:",result)
# print("rssi:",bg95m3.getRSSI())
print(bg95m3.getLocation())

print("Power off")
bg95m3.powerOff()
del bg95m3



