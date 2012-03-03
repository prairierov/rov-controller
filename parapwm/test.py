#import parapwm
#from time import sleep
#parapwm.init()
#parapwm.analogWrite(2,255)
#sleep(1)
#parapwm.analogWrite(2,127)
#sleep(1)
from parapwm_c import *
from parapwm_c.CONST import *
port = Port(LPT1,outmode=LP_DATA_PINS)
port[2].write(10)
port[3].set()
port[3].write(127)
port[4].write(255)
port[5].write(50)
