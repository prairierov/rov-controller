#!/usr/bin/python
# This controls the motors using the parallel port.
#

from getopt import getopt
from serial import Serial
from time import sleep
from sys import *
from PySide.QtCore import *
from PySide.QtGui import *
from threading import Thread
from array import array
import string
from struct import *
import parapwm
from parapin.CONST import *
from select import select
import re
try: from Queue import Queue, Empty
except ImportError: from queue import Queue, Empty

#
# Read command-line options
#
opts, args = getopt(argv[1:], "", ['polulu'])
global polulu
polulu = False
for opt in opts:
    if opt[0] == '--polulu':
        polulu = True
if polulu: print "Polulu mode"

#
# If pins are low, they might draw too much current
#
bad_pins = list()
parapwm.port.set_output_mode(0)
parapwm.port.set_input_mode(LP_DATA_PINS | LP_SWITCHABLE_PINS)
for i in range(1,17):
    pin = parapwm.port[i]
    if pin.is_set() == False:
        print "Pin %d is bad." % i
        bad_pins.append(i)
parapwm.port.set_input_mode(0)
parapwm.port.set_output_mode(LP_DATA_PINS | LP_SWITCHABLE_PINS)

global pins
if polulu:
    pins = [('L/R (1/2/3)<br>', 1), ('F/B (4/5/6)<br>', 4), ('Twist (14/16/17)<br>', 14), ('Slider (7/8/9)<br>', 7)]
else:
    pins = [('L/R (2/3)<br>', 2), ('F/B (4/5)<br>', 4), ('Twist (6/7)<br>', 6), ('Slider (8/9)<br>', 8)]
axis_map = {0: 2, 1: 4, 2: 6, 3: 8}
axis_mult = {0: 1, 1: -1, 2: 1, 3: -1}
button_map = {1: 1, 4: 14, 5: 16, 6: 17}

def get_pin_num(name):
    try:
        index = [y[0] for y in pins].index(name)
        return pins[index][1]
    except ValueError:
        return False
def set_pin(pin, value):
    print pin, "=", value
    sign = 1 if value < 0 else 0
    #if pin == 2: # centered = full power
    #    #parapwm.set_pin(pin, abs(255 - abs(value)))
    #    parapwm.set_pin(pin, 255 if abs(value) < 128 else 0)
    parapwm.set_pin(pin, abs(value))
    if polulu:
        parapwm.set_pin(pin+1, 255 if sign == 0 else 0)
        parapwm.set_pin(pin+2, 0 if sign == 0 else 255)
    else:
        print pin+1, "=", sign*255
        parapwm.set_pin(pin+1, sign*255)

##
## Get the position of the joystick
##
global stick
try:
    stick = open('/dev/input/js0', 'r')
except:
    print "No stick!"
    stick = None
print "joystick:", stick
def js_event(joystick):
    while not select([stick.fileno()], [], [], 1)[0]: False
    data = joystick.read(8)
    info = unpack('LhBB', data)
    if info[2] & 1 > 0:
        return dict(button=info[3], value=(True if info[1] else False))
    else:
        return dict(axis=info[3], value=info[1])
def joythread():
    while True:
        e = js_event(stick)
        if e == None: continue
        #print "joystick:", e
        if 'axis' in e and e['axis'] in axis_map:
            pin = axis_map[e['axis']]
            #value = int(e['value']*128/32768+128)# * axis_mult[e['axis']]
            value = int(e['value']*256/32768) * axis_mult[e['axis']]
            set_pin(pin, value)
            app.newPinValue.emit(pin, value)
        elif 'button' in e and e['button'] in button_map:
            pin = button_map[e['button']]
            value = 255 if e['value'] else 0
            set_pin(pin, 255 if e['button'] else 0)
            
joythread = Thread(target=joythread)
joythread.daemon = True

##
## Displays values for all of the motors
##
class KBSlider(QSlider):
    def keyPressEvent(self, event):
        if event.text().isdigit():
            num = int(event.text())
            if num == 0: num = 10
            self.setValue(int((num-1) * 255 / 9))
        elif event.key() == 16777235: # up
            self.setValue(self.value() + 8)
        elif event.key() == 16777237: # down
            self.setValue(self.value() - 8)
        elif event.key() == 16777236: # right
            QApplication.sendEvent(w, QKeyEvent(QEvent.KeyPress, int(Qt.Key_Tab), Qt.NoModifier, ""))
        elif event.key() == 16777234: # left
            QApplication.sendEvent(w, QKeyEvent(QEvent.KeyPress, int(Qt.Key_Tab), Qt.ShiftModifier, ""))
        else: super(KBSlider, self).keyPressEvent(event)

class PWMLayout(QVBoxLayout):
    def __init__(self, parent=None, name="PWM"):
        super(PWMLayout, self).__init__(parent)
        self.name = name
        self.slider = KBSlider(Qt.Vertical)
        self.slider.setRange(-255, 255)
        self.slider.setTickInterval(127)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.addWidget(self.slider)
        self.slider.valueChanged.connect(self.valueChanged)
        label = QLabel(name)
        self.addWidget(label)
    @Slot(int)
    def valueChanged(self, value):
        #print "name = %s, value = %d" % (self.name, value)
        global arduino_is_setting_pin
        if arduino_is_setting_pin == False:
            set_pin(get_pin_num(self.name), value)

class MainWindow(QDialog):
    def __init__(self, parent=None):
        print "hello"
        super(MainWindow, self).__init__(parent)
        sliders = QHBoxLayout()
        self.pwms = {}
        for (name, pin) in pins:
            pinLayout = PWMLayout(name=name)
            self.pwms[pin] = pinLayout
            sliders.addLayout(pinLayout)
        layout = QVBoxLayout()
        layout.addLayout(sliders)
        if stick == None:
            label = QLabel("<span style='color:red'>No joystick. Plug in a joystick and restart the program.</span>")
            layout.addWidget(label)
        for i in bad_pins:
            print "Bad pin", i
            label = QLabel("<span style='color:darkorange'>Pin %d is low. This is probably bad.</span>" % i)
            layout.addWidget(label)
        self.setLayout(layout)

arduino_is_setting_pin = False
class Application(QApplication):
    newPinValue = Signal(int, int)
    @Slot(int, int)
    def updateSlider(self, pin, value):
        global arduino_is_setting_pin
        arduino_is_setting_pin = True
        try: w.pwms[pin].slider.setValue(value)
        except KeyError: print "Can't set slider that doesn't exist"
        arduino_is_setting_pin = False

app = Application(argv)
joythread.start()
app.newPinValue.connect(app.updateSlider)
w = MainWindow()
w.show()
w.raise_()
w.activateWindow()
app.exec_()
exit()
