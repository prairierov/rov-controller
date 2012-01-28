# This sends a PWM signal over the parallel port.
# It uses the parapin module to individually turn pins on and off.
# It has to be run as root, by typing sudo before the program that uses it.
#
# To use it, run sudo python in the same directory, and type:
# from parapwm import *
# To set a pin, do this:
# set_pin(pin, value)
# pin is 2-9 and value is 0-255

from parapin import *
from parapin.CONST import *
from time import sleep
from sys import *
import threading
from fractions import gcd
from threading import Lock

port = Port(LPT1, outmode=LP_DATA_PINS)

pwmthread = None
pins = []
pinslock = Lock()
# Used internally to turn pins on and off
def do_pwm_thread():
    thread = threading.currentThread()
    cycle_len = 256
    print pins
    while True:
        i = 0
        while i < cycle_len:
            for pin in range(0, len(pins)):
                if pins[pin] == -1: continue
                if i < pins[pin]:
                    port.get_pin(pin).set()
                else:
                    port.get_pin(pin).clear()
            sleep(0.00001)
            i += 1

def set_pin(pin, cycle):
    pinslock.acquire()
    for i in range(len(pins), pin + 1):
        pins.insert(i, -1)
    pins[pin] = cycle
    pinslock.release()
    global pwmthread
    if not pwmthread:
        pwmthread = threading.Thread(target=do_pwm_thread, args=())
        pwmthread.daemon = True
        pwmthread.start()
