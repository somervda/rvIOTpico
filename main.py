
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

print("Main Start")
led.on()
time.sleep(2)
led.off()
time.sleep(2)

try:
    print("Main check for user button")
    if userButton.value() == 0:
        print("Exit main - user button pressed")
        led.on()
        time.sleep(1)
        led.off()
    else:
        # 4 flashes indicate mainloop is starting
        for x in range(4):
            ledFlash()
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