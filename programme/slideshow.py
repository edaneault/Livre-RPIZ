import sys
import signal
import time
import struct
import serial
import RPi.GPIO as GPIO

# Eink comm frame
def buildFrame(code, params=[]):
    header = 0xA5
    footer = 0xCC33C33C
     
    param_len = 0
    for param in params:
        param_len = param_len + len(param)
            
    # header, length, cmd, parameter, footer, xor
    frame_len  = 1 + 2 + 1 + param_len + 4 + 1

    frame = bytearray()
    frame.append(header)
    frame += bytearray(struct.pack('>H', frame_len))
    frame.append(code)
    for param in params:
        frame += param 
    frame += bytearray(struct.pack('>I', footer))
    xor = 0
    for byte in frame:
        xor = xor ^ byte
    frame.append(xor)

    return frame

# Serial wrapper 
sp = serial.Serial("/dev/serial0", baudrate = 115200, timeout=0.2)

def writeToSerial(frame):
    sp.write(frame)

def transactOnSerial(frame):
    sp.write(frame)
    
    reply = bytearray()
    # Attendre longtemps pour premier octet
    sp.timeout = 5
    newByte = sp.read()

    # Ne pas attendre longtemps pour le reste
    sp.timeout = 0.2
    while newByte != b'':
        reply += newByte
        newByte = sp.read()

    return reply

def readFromSerial(numberOfBytes=1):
    return sp.read(numberOfBytes)

def changeSerialBaudrate(baudrate):
    sp.baudrate = baudrate

def flushInputSerial():
    sp.reset_input_buffer()

# Eink API
def shakeHand():
    return transactOnSerial(buildFrame(0x00)) == bytearray(b'OK')
        
def setBaudrate(baudrate):
    writeToSerial(buildFrame(0x01, [struct.pack('>I', baudrate)]))
    time.sleep(1)
    
def getBaudrate():
    return transactOnSerial(buildFrame(0x02)).decode("ASCII")
    
def getStorageArea():
    area = transactOnSerial(buildFrame(0x06))

    if area == b'0':
        return "NAND"
    
    if area == b'1':
        return "SD"
    
    raise ValueError('Unexpected value received', area)
    
def setStorageArea(area):
    if area == "NAND":
        areaByte = b'\x00'
    else:
        if area == "SD":
            areaByte = b'\x01'
        else:
            raise ValueError('Value must be NAND or SD, received : ', area)
            
    return transactOnSerial(buildFrame(0x07, [areaByte])) == bytearray(b'OK')
    
def sleep():
    writeToSerial(buildFrame(0x08))
    
def refresh():
    return transactOnSerial(buildFrame(0x0A)) == bytearray(b'OK')
    
def getOrientation():
    orientation = transactOnSerial(buildFrame(0x0C))

    match orientation:
        case b'0':
            return "0deg"
        case b'1':
            return "90deg"
        case b'2':
            return "180deg"
        case b'3':
            return "270deg"
        case other:
            raise ValueError('Unexpected value received', area)
    
def setOrientation(orientation):
    match orientation:
        case "0deg":
            orientationByte = b'\x00'
        case "90deg":
            orientationByte = b'\x01'
        case "180deg":
            orientationByte = b'\x02'
        case "270deg":
            orientationByte = b'\x03'
        case other:
            raise ValueError('Value must be 0deg, 90deg, 180deg or 270 deg, received : ', orientation)

    return transactOnSerial(buildFrame(0x0D, [orientationByte])) == bytearray(b'OK')
            
def importFontLibrary():
    pass
    
def importImage():
    pass
    
def setColor(fgcolor, bgcolor):
    return transactOnSerial(buildFrame(0x10, [struct.pack('B', fgcolor), struct.pack('B', bgcolor)])) == bytearray(b'OK')
    
def getColor():
    return transactOnSerial(buildFrame(0x11))
    
def getEnglishFontSize():
    return transactOnSerial(buildFrame(0x1C))
    
def getFontSize():
    return transactOnSerial(buildFrame(0x1D))
    
def setEnglishFontSize(size):
    return transactOnSerial(buildFrame(0x1E, [struct.pack('B', size)]))
    
def setFontSize(size):
    return transactOnSerial(buildFrame(0x1F, [struct.pack('B', size)]))
    
def drawPoint(x, y):
    return transactOnSerial(buildFrame(0x20, [struct.pack('>H', x), struct.pack('>H', y)])) == bytearray(b'OK')
    
def drawLine(x1, y1, x2, y2):
    return transactOnSerial(buildFrame(0x22, [struct.pack('>H', x1), struct.pack('>H', y1), struct.pack('>H', x2), struct.pack('>H', y2)])) == bytearray(b'OK')
    
def fillRectangle(x1, y1, x2, y2):
    return transactOnSerial(buildFrame(0x24, [struct.pack('>H', x1), struct.pack('>H', y1), struct.pack('>H', x2), struct.pack('>H', y2)])) == bytearray(b'OK')
    
def drawRectangle(x1, y1, x2, y2):
    return transactOnSerial(buildFrame(0x25, [struct.pack('>H', x1), struct.pack('>H', y1), struct.pack('>H', x2), struct.pack('>H', y2)])) == bytearray(b'OK')
    
def drawCircle(x, y, r):
    return transactOnSerial(buildFrame(0x26, [struct.pack('>H', x), struct.pack('>H', y), struct.pack('>H', r)])) == bytearray(b'OK')
    
def fillCircle(x, y, r):
    return transactOnSerial(buildFrame(0x27, [struct.pack('>H', x), struct.pack('>H', y), struct.pack('>H', r)])) == bytearray(b'OK')
    
def drawTriangle(x1, y1, x2, y2, x3, y3):
    return transactOnSerial(buildFrame(0x28, [struct.pack('>H', x1), struct.pack('>H', y1), struct.pack('>H', x2), struct.pack('>H', y2), struct.pack('>H', x3), struct.pack('>H', y3)])) == bytearray(b'OK')
    
def fillTriangle(x1, y1, x2, y2, x3, y3):
    return transactOnSerial(buildFrame(0x29, [struct.pack('>H', x1), struct.pack('>H', y1), struct.pack('>H', x2), struct.pack('>H', y2), struct.pack('>H', x3), struct.pack('>H', y3)])) == bytearray(b'OK')
    
def clear():
    return transactOnSerial(buildFrame(0x2E)) == bytearray(b'OK')
    
def drawText(x, y, text):
    return transactOnSerial(buildFrame(0x30, [struct.pack('>H', x), struct.pack('>H', y), bytearray(text, 'ASCII') + b'\x00'])) == bytearray(b'OK')
    
def displayImage(x, y, filename):
    return transactOnSerial(buildFrame(0x70, [struct.pack('>H', x), struct.pack('>H', y), bytearray(filename, 'ASCII') + b'\x00']))
    
def sendtoSD(filename):
    pass
def nandFullErase():
    pass

# Wakeup, Boutons et callbacks
GPIO.setmode(GPIO.BCM) # Système basé sur les # de GPIOs

wakeupGPIO = 22
GPIO.setup(wakeupGPIO, GPIO.OUT)
def wakeup():
    GPIO.output(wakeupGPIO, 1)
    time.sleep(0.2)
    GPIO.output(wakeupGPIO, 0)
    flushInputSerial()

backBTN_GPIO = 24
fwdBTN_GPIO = 25
goBTN_GPIO = 27

GPIO.setup(backBTN_GPIO, GPIO.IN)
GPIO.setup(fwdBTN_GPIO, GPIO.IN)
GPIO.setup(goBTN_GPIO, GPIO.IN)

# Suivi des événements
events = ['NOTHING']

# Affect screen with IMAGE
images = ['MAIS.BMP', 'KID.BMP', 'ZEN.BMP']
def wakeUpandUpdate(index):
    wakeup()
    clear()
    displayImage(0, 0, images[index])
    refresh()
    sleep()

# Callback
pictureIndex = 0
def shortLongCallback(channel):
    misses = 0
    for i in range(10):
        if GPIO.input(channel) == 1:
            misses += 1
            
        if misses >= 2:
            # Short
            # events.append('short' + str(channel))
            if channel == backBTN_GPIO:
                global pictureIndex 
                pictureIndex = 0
            else:
                if channel == fwdBTN_GPIO:
                    pictureIndex = 1
                else:
                    pictureIndex = 2
            return
        else:
            time.sleep(0.1)

    # Long
    # events.append('long' + str(channel))

GPIO.add_event_detect(backBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)
GPIO.add_event_detect(fwdBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)
GPIO.add_event_detect(goBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)

# Remettre en état
wakeup()
clear()
refresh()
refresh()

# Config SD
if not setStorageArea("SD"):
    print("Couldn't set storage area")
    sys.exit()

# Register le CTRL+C
def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

oldIndex = 555
while True:
    if oldIndex != pictureIndex:
        wakeUpandUpdate(pictureIndex)
        oldIndex = pictureIndex

    time.sleep(1)

#    indexInList += 1
#    if indexInList == len(images):
#        indexInList = 0
