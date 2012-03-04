from parapwm_c import *
from parapwm_c.CONST import *
import threading
from threading import Thread

global port
port = None

def test():
    print "hi"

def init():
    global port
    if not port: port = Port(LPT1, outmode=LP_DATA_PINS)
def get_port():
    global port
    init()
    return port
def set(pin):
    global port
    init()
    port[pin].set()
def clear(pin):
    global port
    init()
    port[pin].clear()
def pulse(pin, cycle):
    global port
    init()
    TIME = .01
    non = TIME / (abs(cycle)/255.)
    noff = TIME - non
    while not threading.currentThread().cancelled():
        port[pin].pulse(0, int(non), 0, int(noff), int(1./TIME))
    #print "done"
def analogWrite(pin, cycle):
    global port
    port[pin].write(cycle)

#global pwmthreads
#pwmthreads = []
#pins = []
#
#class cancellablethread(Thread):
#    def __init__(self, *args, **kwargs):
#        Thread.__init__(self, *args, **kwargs)
#        self._cancelled = False
#    def cancel(self):
#        self._cancelled = True
#    def cancelled(self):
#        return self._cancelled
#
#def analogWrite(pin, cycle):
#    for i in range(len(pins), pin + 1):
#        pins.insert(i, -1)
#    pins[pin] = cycle
#    global pwmthreads
#    for i in range(len(pwmthreads), pin + 1):
#        pwmthreads.insert(i, None)
#    if pwmthreads[pin] != None:
#        pwmthreads[pin].cancel()
#    pwmthread = cancellablethread(target=pulse, args=(pin, cycle))
#    pwmthread.daemon = True
#    pwmthread.start()
