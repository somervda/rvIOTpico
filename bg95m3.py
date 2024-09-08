# class to wrape the BG95-M3 LTE modem functionality
# on the Sixfab LTE Pico board

import time

from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

class Bg95m3:
    picoLTE = None
    def __init__(self): 
        self.picoLTE = PicoLTE()
        self.picoLTE.network.register_network()
        self.picoLTE.http.set_context_id()
        self.picoLTE.network.get_pdp_ready()


    def send(self,url):
        self.picoLTE.http.set_server_url(url)
        result = self.picoLTE.http.get()
        # Read the response after 2 seconds.
        time.sleep(2)
        result = self.picoLTE.http.read_response()
        print(result)
        if result["status"] == Status.SUCCESS:
            return True
        else:
            return False

    def getRSSI(self):
        command = "AT+CSQ"
        result = self.picoLTE.atcom.send_at_comm(command)
        rssi= result['response'][0].split(":")[1].split(',')[0]
        return (int(rssi.strip())*2)-109


    def getLocation(self):
         # First go to GNSS prior mode and turn on GPS.
        startTime = time.time()
        self.picoLTE.gps.set_priority(0)
        time.sleep(3)
        self.picoLTE.gps.turn_on()
        debug.info("Trying to fix GPS...")

        for x in range(0, 60):
            result = self.picoLTE.gps.get_location()
            print(".", end='')

            if result["status"] == Status.SUCCESS:
                loc = result.get("value")
                response = result.get("response")[0].split(",")
                t = response[0].split(" ")[1].split(".")[0]
                d = response[9]
                back = {"latitude":loc[0],"longitude":loc[1],"date":d,"time":t,"duration":time.time() - startTime}
                return back
            time.sleep(5)  # 60*5 = 3 minutes timeout for GPS fix.
        return None

    def powerOff(self):
        self.picoLTE.base.power_off()

