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
import re
try: from Queue import Queue, Empty
except ImportError: from queue import Queue, Empty

pins = [('L/R (9)<br>', 2), ('F/B (10)<br>', 4), ('Twist (11)<br>', 6), ('Slider (3)<br>', 8),('Button<br>L/R (5)', 7), ('Button<br>F/B (6)', 9)]
axis_map = {0: 2, 1: 4, 2: 6, 3: 8, 4: 7, 5: 9}
axis_mult = {0: 1, 1: -1, 2: 1, 3: 1, 4: 1, 5: -1}

##
## Code for controlling Arduino, doesn't actually do anything
## To control the Arduino, use arduino.py instead
##
port = '/dev/ttyACM0'
(opts, args) = getopt(argv[1:], 'p:')
for (opt, val) in opts:
    if opt == '-p':
        port = val

global arduino
try: arduino = Serial(port, 19200)
except:
    print "Arduino: failed to connect"
    arduino = None

def writer_thread(fh, queue):
    for line in iter(queue.get, ''):
        try:
            app.sigIsWriting.emit()
            fh.write(line)
            app.sigIsWaiting.emit()
        except:
            print "While writing:", exc_info()[0]
            app.sigWriteFailed.emit()
def reader_thread(fh, queue):
    if fh == None:
        print "No arduino"
        return
    chars = array('c')
    while True:
        char = fh.read(1)
        if len(char) == 0:
            app.sigWriteFailed.emit()
        chars.append(char[0])
        #print "%d %s" % (ord(char[0]), char)
        if char == '\n' or char == '\r':
            if len(chars) == 0: continue # ignore empty line
            msg = chars.tostring()
            amatch = re.match(r"^ANA([0-9])([0-9A-z]{4})$", msg)
            if amatch:
                print "analog msg", msg
                apin = amatch.group(1)
                avalue = int(amatch.group(2), 16)
                print "analog", apin, "=", avalue
            elif string.find(msg, "\xDE\xAD\xBE\xEF") == -1:
                print "got %s" % msg
            else:
                # Set sliders to values from Arduino
                print "deadbeef"
                data = msg[4:-1] # skip first 4 bytes and newline
                remainder = len(data) % 4
                if remainder != 0: data = data[0:-(4-remainder)]
                bytestring = data.decode('hex')
                for i in xrange(0, len(bytestring), 2):
                    pin = ord(bytestring[i])
                    value = ord(bytestring[i+1])
                    print pin, "=", value
                    app.newPinValue.emit(pin, value)
            queue.put(msg)
            chars = array('c')
outqueue = Queue() # output for Arduino
inqueue = Queue() # input from Arduino
outthread = Thread(target=writer_thread, args=(arduino, outqueue))
outthread.daemon = True
inthread = Thread(target=reader_thread, args=(arduino, inqueue))
inthread.daemon = True
outthread.start()
inthread.start()

def get_pin_num(name):
    try:
        index = [y[0] for y in pins].index(name)
        return pins[index][1]
    except ValueError:
        return False
def set_pin(pin, value):
    print pin, "=", value
    sign = 1 if value < 0 else 0
    parapwm.set_pin(pin, abs(value))
    parapwm.set_pin(pin+1, sign*255)

##
## Get the position of the joystick
##
stick = open('/dev/input/js0', 'r')
print "joystick:", stick
def js_event(joystick):
    data = joystick.read(8)
    info = unpack('LhBB', data)
    if info[2] & 1 > 0:
        return dict(button=info[3], value=info[1])
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
            value = int(e['value']*256/32768)
            set_pin(pin, value)
            app.newPinValue.emit(pin, value)
joythread = Thread(target=joythread)

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
        self.slider.setRange(0, 255)
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
            app.sigIsWriting.emit()

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
        self.statusLabel = QLabel("Do something...")
        layout = QVBoxLayout()
        layout.addLayout(sliders)
        layout.addWidget(self.statusLabel)
        button = QPushButton("Reload")
        button.clicked.connect(lambda: outqueue.put("deadbeef\n"))
        layout.addWidget(button)
        self.setLayout(layout)

arduino_is_setting_pin = False
class Application(QApplication):
    sigIsWriting = Signal()
    sigWriteFailed = Signal()
    sigIsWaiting = Signal()
    sigSynchronized = Signal()
    newPinValue = Signal(int, int)
    def isWriting(self):
        w.statusLabel.setText("Writing to Arduino...")
    def writeFailed(self):
        w.statusLabel.setText("<font color='red'>Epic fail</font>")
    def isWaiting(self):
        w.statusLabel.setText("Waiting for Arduino...")
    def isSynchronized(self):
        w.statusLabel.setText("Synchronized")
    @Slot(int, int)
    def updateSlider(self, pin, value):
        global arduino_is_setting_pin
        arduino_is_setting_pin = True
        try: w.pwms[pin].slider.setValue(value)
        except KeyError: print "Can't set slider that doesn't exist"
        arduino_is_setting_pin = False
    #sigIsWriting.connect(isWriting)
    #sigWriteFailed.connect(writeFailed)
    #sigIsWaiting.connect(isWaiting)

app = Application(argv)
joythread.start()
app.sigIsWriting.connect(app.isWriting)
app.sigIsWaiting.connect(app.isWaiting)
app.sigWriteFailed.connect(app.writeFailed)
app.sigSynchronized.connect(app.isSynchronized)
app.newPinValue.connect(app.updateSlider)
w = MainWindow()
def arduinoStatus():
    for received in iter(inqueue.get, ''):
        if inqueue.empty() and outqueue.empty(): app.sigSynchronized.emit()
        else: app.sigIsWriting.emit()
statusThread = Thread(target=arduinoStatus)
statusThread.daemon = True
statusThread.start()
w.show()
app.exec_()
exit()
