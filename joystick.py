#!/usr/bin/python
# This example prints the value from the joystick whenever it gets changed

from struct import *
from select import select

joystick = open("/dev/input/js0", 'r')

def js_event(joystick):
    while not select([joystick.fileno()], [], [], 1)[0]: False
    data = joystick.read(8)
    info = unpack('LhBB', data)
    if info[2] & 1 > 0:
        return dict(button=info[3], value=True if info[1] else False)
    else:
        return dict(axis=info[3], value=info[1])

while True: print js_event(joystick)
