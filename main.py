
import machine
import sys
import time

# main.py is run automatically when powered on or reset
# Any exception in mainloop will result in a exception.txt
# to be written 
# Looks like you can interrupt execution anytime by issuing a 
# mpremote command in vscode

led = machine.Pin("LED", machine.Pin.OUT)
def ledFlash():
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.2)

ledFlash()
time.sleep(2)

try:
    import mainloop
except Exception as e:
    f=open('exception.txt', 'w')  
    f.write(str(time.localtime()) + "\n")
    sys.print_exception(e,f)
    f.close()
    # 10 flashes indicate exception occurred
    for n in range(10):
        ledFlash()
    machine.reset()