import parapwm
from time import sleep
parapwm.init()
parapwm.analogWrite(2,255)
sleep(1)
parapwm.analogWrite(2,127)
sleep(1)
