import network
import machine
import time
from settings import Settings
from microWebCli import MicroWebCli

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
        self.wlan = network.WLAN(network.STA_IF)
        not self.quiet and print("Connecting to " + self.settings.get("SSID") + ":")
        self.wlan.active(True)
        # Note SSID is case sensitive i.e. make sure it is gl24 not GL24
        network.hostname(self.settings.get("HOSTNAME"))
        self.wlan.connect(self.settings.get("SSID"), self.settings.get("PASSWORD"))
        connectCount = 0
        while not self.wlan.isconnected() and self.wlan.status() >= 0:
            connectCount+=1
            if connectCount>30:
                not self.quiet and print(" wifi connect timed out")
                self.powerOff()
                return False
            # Slow LED flash while connecting
            not self.quiet and print(".", end="")
            self.ledFlash()

        time.sleep(2)
        not self.quiet and print("Connected! ifconfig:",self.wlan.ifconfig()[0],self.wlan.ifconfig()[1],self.wlan.ifconfig()[2],self.wlan.ifconfig()[3])
        return True

    def send(self,url):
        not self.quiet and print("wifi send:",url)
        try:
            wCli = MicroWebCli(url)
            wCli.OpenRequest()
            buf = memoryview(bytearray(1024))
            resp = wCli.GetResponse()
            if resp.IsSuccess():
                if not resp.IsClosed():
                    x = resp.ReadContentInto(buf)
                    if x < len(buf):
                        buf = buf[:x]
                    not self.quiet  and print(str(bytearray(buf), "utf-8"))
                not self.quiet  and print(
                    'Ok Response:' ,resp.GetStatusCode(),resp.ReadContent())
                return True
            else:
                not self.quiet  and print(
                    'Fail Response:'  ,resp.GetStatusCode(),resp.ReadContent(),retryCount)
                return False
        except Exception as error:
            # handle the exception
            not self.quiet  and print("An exception occurred:", error)
            return False

    def powerOff(self):
        not self.quiet and print("iotwifi power off")
        self.wlan.disconnect()
        self.wlan.active(False)
        self.wlan.deinit()