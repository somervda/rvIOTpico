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
        except:
            print("Error: powerOn")
            return None
        # Success return None
        return True

    def lteConnect(self):
        try:
            not self.quiet and print("lteConnect")
            # command = "AT+CSQ"
            # result = self.picoLTE.atcom.send_at_comm(command)
            # not self.quiet and print( "Reset AT to factory", result)
            # if result["status"] != Status.SUCCESS :
            #     print("Error: Reset AT to factory", result)
                # return None

            # command = "AT+COPS"
            # result = self.picoLTE.atcom.send_at_comm(command)
            # not self.quiet and print( "Get available networks (AT+COPS=?) ", result)
        

            # See https://arduino103.blogspot.com/2024/02/sixfab-pico-lte-premier-test-de.html  
            # Good result is 1 or 5
            # 0: Not registered, the device is currently not searching for new operator.
            # 1: Registered to home network.
            # 2: Not registered, but the device is currently searching for a new operator.
            # 3: Registration denied.
            # 4: Unknown. For example, out of range.
            # 5: Registered, roaming. The device is registered on a foreign (national or international) network.
            not self.quiet and print( "Registering Network...")
            result = self.picoLTE.network.register_network()
            not self.quiet and print( "Register Network", result)
            if result["status"] != Status.SUCCESS :
                print("Error: Register Network", result)
                return None
            result = self.picoLTE.http.set_context_id()
            not self.quiet and print( "set_context_id", result)
            if result["status"] != Status.SUCCESS:
                print("Error: set_context_id",result)
                return None
            result = self.picoLTE.network.get_pdp_ready() 
            not self.quiet and print( "get_pdp_ready", result)
            if result["status"] != Status.SUCCESS :
                print("Error: get_pdp_ready",result)
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
            time.sleep(5)
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
            not self.quiet and print("getRSSI", result)
            rssi= result['response'][0].split(":")[1].split(',')[0]
            if int(rssi.strip()) == 99:
                print("CSQ unknown or not detectable - 99")
                return None
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

    def check_apn(self):
        result = self.picoLTE.network.check_apn()
        print("check_apn:", result)

    def check_network_registration(self):
        result = self.picoLTE.network.check_network_registration()
        print("check_network_registration:", result)

    def check_pdp_context_status(self):
        result = self.picoLTE.network.check_pdp_context_status()
        print("check_pdp_context_status", result)

    def factory_reset(self):
        not self.quiet and print("Factory Reset...")
        command = "AT+CSQ"
        result = self.picoLTE.atcom.send_at_comm(command)
        not self.quiet and print( "Reset AT to factory", result)
        if result["status"] != Status.SUCCESS :
            print("Error: Reset AT to factory", result)
            return None

    def get_available_networks(self):
        command = "AT+COPS"
        result = self.picoLTE.atcom.send_at_comm(command)
        not self.quiet and print( "Get available networks (AT+COPS=?) ", result)


