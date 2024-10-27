import network
import machine
import time
from settings import Settings
# from microWebCli import MicroWebCli
import requests

class IOTWifi:

    quiet = True
    wifi = None
    led = machine.Pin("LED", machine.Pin.OUT)
    settings = None


    def __init__(self,quiet=True):
        not self.quiet and print('__init__',quiet)
        self.quiet = quiet
        self.settings = Settings()

    def ledFlash(self):
        self.led.on()
        time.sleep(0.08)
        self.led.off()
        time.sleep(0.1)
        self.led.on()
        time.sleep(0.08)
        self.led.off()
        time.sleep(0.8)

    def connect(self):
        not self.quiet and print("Connecting to wifi")
        SSID = ""
        PASSWORD = ""
        # Try connecting with up to 5 different SSIDs
        for ssidIndex in range(1,5):
            if ssidIndex ==1:
                SSID=self.settings.get("SSID01")
                PASSWORD=self.settings.get("PASSWORD01")
            if ssidIndex ==2:
                SSID=self.settings.get("SSID02")
                PASSWORD=self.settings.get("PASSWORD02")
            if ssidIndex ==3:
                SSID=self.settings.get("SSID03")
                PASSWORD=self.settings.get("PASSWORD03")
            if ssidIndex ==4:
                SSID=self.settings.get("SSID04")
                PASSWORD=self.settings.get("PASSWORD04")
            if ssidIndex ==5:
                SSID=self.settings.get("SSID05")
                PASSWORD=self.settings.get("PASSWORD05")
            not self.quiet and print("ssidIndex:",ssidIndex,SSID,PASSWORD)
            if SSID == None:
                return False
            else:
                if self.tryConnect(self.settings.get("HOSTNAME"),SSID, PASSWORD):
                     not self.quiet and print("Connected! ifconfig:",self.wlan.ifconfig()[0],self.wlan.ifconfig()[1],self.wlan.ifconfig()[2],self.wlan.ifconfig()[3])
                     return True
        return False


    def tryConnect(self,HOSTNAME,SSID,PASSWORD):
        not self.quiet and print("Trying to connecting to " + SSID)
        # Note SSID is case sensitive i.e. make sure it is gl24 not GL24
        # Connection status is 
        # 0   STAT_IDLE -- no connection and no activity,
        # 1   STAT_CONNECTING -- connecting in progress,
        # -3  STAT_WRONG_PASSWORD -- failed due to incorrect password,
        # -2  STAT_NO_AP_FOUND -- failed because no access point replied,
        # -1  STAT_CONNECT_FAIL -- failed due to other problems,
        # 3   STAT_GOT_IP -- connection successful.
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        network.hostname(HOSTNAME)
        self.wlan.connect(SSID,PASSWORD)
        connectCount = 0
        while not self.wlan.isconnected() and self.wlan.status() !=3:
            connectCount+=1
            if connectCount>30:
                not self.quiet and print(SSID + " wifi connect timed out")
                self.powerOff()
                return False
            # Slow LED flash while connecting
            not self.quiet and print(".", end="")
            self.ledFlash()
        return True

    def send(self,url):
        not self.quiet and print("wifi send:",url)
        self.ledFlash()

        try:
            resp = requests.get(url)
            not self.quiet and print("wifi send status:",resp.status_code)
            if resp.status_code==200:
                return True
            else:
                not self.quiet  and print(
                    'Fail Response:'  ,resp.status_code,resp,text)
                return False
        except Exception as error:
            # handle the exception
            not self.quiet  and print("A wifi exception occurred:", error)
            return False

    def powerOff(self):
        not self.quiet and print("iotwifi power off")
        self.wlan.disconnect()
        self.wlan.active(False)
        self.wlan.deinit()