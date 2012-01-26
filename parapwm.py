from parapin import *
from parapin.CONST import *
from time import sleep
from sys import *
import threading
from fractions import gcd
from threading import Lock

port = Port(LPT1, outmode=LP_DATA_PINS)

class PWMThread(threading.Thread):
    def __init__(self, target=None, args=None):
        super(PWMThread, self).__init__(target=target, args=args)
        self._stop = threading.Event()
    def stop(self):
        self._stop.set()
    def stopped(self):
        return self._stop.isSet()

pwmthread = None
pins = []
pinslock = Lock()
def do_pwm_thread():
    thread = threading.currentThread()
    cycle_len = 256
    #cycle_gcd = gcd(cycle, cycle_len)
    #if cycle_gcd > 0:
    #    cycle /= cycle_gcd
    #    cycle_len /= cycle_gcd
    print pins
    while True:#thread.stopped():
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
    #if pin in threads:
    #    threads[pin].stop()
    #    del threads[pin]
    #thread = PWMThread(target=pwm_thread, args=(port.get_pin(pin), cycle))
    #threads[pin] = thread
    #thread.start()
    pinslock.acquire()
    for i in range(len(pins), pin + 1):
        pins.insert(i, -1)
    pins[pin] = cycle
    pinslock.release()
    global pwmthread
    if not pwmthread:
        pwmthread = PWMThread(target=do_pwm_thread, args=())
        pwmthread.daemon = True
        pwmthread.start()
