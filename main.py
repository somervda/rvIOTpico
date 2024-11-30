
import machine
import sys
import time

# main.py is run automatically when powered on or reset
# Any exception in mainloop will result in a exception.txt
# to be written 
# Press the user button on the sixfab pico board
# to exit the main loop and get access to REPL

led = machine.Pin("LED", machine.Pin.OUT)
userButton = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_DOWN)
def ledFlash():
    led.on()
    time.sleep(0.2)
    led.off()
    time.sleep(0.1)

for n in range(10):
    ledFlash()


try:
    if True:
        if userButton.value() == 0:
            print("Exit mainLoop - user button pressed")
            for x in range(4):
                ledFlash()
            sys.exit(0)
        import mainloop
except Exception as e:
    f=open('exception.txt', 'a')  
    f.write(str(time.localtime()) + "\n")
    sys.print_exception(e,f)
    f.close()
    # 100 fast flashes indicate exception occurred
    for n in range(100):
        ledFlash()
    machine.reset()

print("exit Main")