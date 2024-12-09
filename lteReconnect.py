#!/usr/bin/python3

# This code continuously try's to connect and register the sixfab pico on the lye network
# It can be very hard to get the sixfab device to register after it it loses registration (for some reason)
# but it seems like if you continuously do it for a while it will eventually succeed (Maybe after 2 or 3 hours)


from bg95m3 import Bg95m3
import time
startTime = time.time()

for x in range(100):
    print("\nLoop:",x," seconds:", time.time() - startTime)
    bg95m3 = Bg95m3(False)
    if not bg95m3.powerOn():
        bg95m3.powerOff()
    else:
        print("rssi:",bg95m3.getRSSI())
        bg95m3.lteConnect()
        if bg95m3.getRSSI() != None :
            print("\nConnection successful: try a get")
            url = "http://somerville.noip.me:37007/hello"
            result=bg95m3.httpGet(url)
            print("get result:",result)
            bg95m3.powerOff()
            break
        print("rssi:",bg95m3.getRSSI())

        print("Power off")
        bg95m3.powerOff()
        del bg95m3