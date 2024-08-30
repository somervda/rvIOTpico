"""
Example code for performing GET request to a server with using HTTP.

Example Configuration
---------------------
Create a config.json file in the root directory of the PicoLTE device.
config.json file must include the following parameters for this example:

config.json
{
    "https":{
        "server":"[HTTP_SERVER]",
        "username":"[YOUR_HTTP_USERNAME]",
        "password":"[YOUR_HTTP_PASSWORD]"
    },
}
"""

import time
from pico_lte.utils.status import Status
from pico_lte.core import PicoLTE
from pico_lte.common import debug

picoLTE = PicoLTE()

picoLTE.network.register_network()
picoLTE.http.set_context_id()
picoLTE.network.get_pdp_ready()
picoLTE.http.set_server_url()


debug.info("Sending a GET request.")

result = picoLTE.http.get()
debug.info(result)

# Read the response after 5 seconds.
time.sleep(5)
result = picoLTE.http.read_response()
debug.info(result)
if result["status"] == Status.SUCCESS:
    debug.info("Get request succeeded.")



debug.info("Get GPS")
# First go to GNSS prior mode and turn on GPS.
picoLTE.gps.set_priority(0)
time.sleep(3)
picoLTE.gps.turn_on()
debug.info("Trying to fix GPS...")

for x in range(0, 90):
    result = picoLTE.gps.get_location()
    debug.info(x,result)

    if result["status"] == Status.SUCCESS:
        debug.debug("GPS Fixed. Getting location data...")

        loc = result.get("value")
        debug.info("Lat-Lon:", loc)
        loc_message = ",".join(word for word in loc)

        fix = True
        break
    time.sleep(5)  # 60*5 = 90 seconds timeout for GPS fix.

# Power off modem after request
picoLTE.base.power_off()



