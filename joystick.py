# This example prints the value from the joystick whenever it gets changed

from struct import *

joystick = open("/dev/input/js0", 'r')

def js_event(joystick):
    data = joystick.read(8)
    info = unpack('LhBB', data)
    if info[2] & 1 > 0:
        return dict(button=info[3], value=True if info[1] else False)
    else:
        return dict(axis=info[3], value=info[1])

while True: print js_event(joystick)
