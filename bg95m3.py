# class to wrape the BG95-M3 LTE modem functionality
# on the Sixfab LTE Pico board

import time

from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

class Bg95m3:
    picoLTE = None
    quiet=True
    def __init__(self,quiet=True): 
        self.quiet = quiet
        return None
    
    def powerOn(self):
        try:
            not self.quiet and print("Bg95m3 powerOn")
            self.picoLTE = PicoLTE()
            if self.picoLTE.network.register_network()["status"] != Status.SUCCESS :
                print("Error: Register Network")
                return None
            if self.picoLTE.http.set_context_id()["status"] != Status.SUCCESS:
                print("Error: set_context_id")
                return None
            if self.picoLTE.network.get_pdp_ready()["status"] != Status.SUCCESS :
                print("Error: get_pdp_ready")
                return None
        except:
            print("Error: powerOn")
            return None
        # Success return None
        return True


    def httpGet(self,url):
        try:
            self.picoLTE.http.set_server_url(url)
            result = self.picoLTE.http.get()
            # not self.quiet and print(result)
            # Read the response after 5 seconds.
            time.sleep(2)
            result = self.picoLTE.http.read_response()
            not self.quiet and print(result)
            if result["status"] == Status.SUCCESS:
                return True
            else:
                return False
        except:
            print("Error: httpGet")
            return None

    def getRSSI(self):
        try:
            command = "AT+CSQ"
            result = self.picoLTE.atcom.send_at_comm(command)
            rssi= result['response'][0].split(":")[1].split(',')[0]
            return (int(rssi.strip())*2)-109
        except:
            print("Error: getRSSI")
            return None


    def getLocation(self):
         # First go to GNSS prior mode and turn on GPS.
        try:
            self.picoLTE.gps.set_priority(0)
            time.sleep(3)
            self.picoLTE.gps.turn_on()
            not self.quiet and print("Trying to fix GPS...", end='')

            for x in range(0, 60):
                result = self.picoLTE.gps.get_location()
                not self.quiet and print(".", end='')

                if result["status"] == Status.SUCCESS:
                    loc = result.get("value")
                    not self.quiet and print("GPS response:",result.get("response"))
                    response = result.get("response")[0].split(",")
                    gpsTime = response[0].split(" ")[1].split(".")[0]
                    gpsDate = response[9]
                    year = int(gpsDate[4:6]) + 2000
                    month = int(gpsDate[2:4])
                    day = int(gpsDate[:2])
                    hour = int(gpsTime[:2])
                    minute = int(gpsTime[2:4])
                    second = int(gpsTime[4:6])
                    gpsInfo = {"latitude":float(loc[0]),
                    "longitude":float(loc[1]),
                    "year":year,
                    "month":month,
                    "day":day,
                    "hour":hour,
                    "minute":minute,
                    "second":second}
                    self.picoLTE.gps.turn_off()
                    return gpsInfo
                time.sleep(5)  # 60*5 = 3 minutes timeout for GPS fix.
            return None
        except:
            print("Error: getLocation")
            self.picoLTE.gps.turn_off()
            return None

    def powerOff(self):
        not self.quiet and print("Bg95m3 powerOff")
        self.picoLTE.base.power_off()

