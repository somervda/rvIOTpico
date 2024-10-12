from bg95m3 import Bg95m3
import time


bg95m3 = Bg95m3(False)
if not bg95m3.powerOn():
    bg95m3.powerOff()
else:
    # url = "http://somerville.noip.me:37007/status?user=david"
    # url = 'http://somerville.noip.me:37007/write?iotData={"user":"david","sensorTimestamp":1725910379,"deviceID":7,"latitude":40%2E17483,"longitude":%2D75%2E30221,"appID":3}'
    # result=bg95m3.httpGet(url)
    # print("send:",result)
    # result=bg95m3.httpGet(url)
    # print("send:",result)
    # print("rssi:",bg95m3.getRSSI())
    # print(bg95m3.getLocation())
    print("rssi:",bg95m3.getRSSI())
    bg95m3.lteConnect()
    print("rssi:",bg95m3.getRSSI())

    print("Power off")
    bg95m3.powerOff()
    del bg95m3



