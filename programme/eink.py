import os
import sys
import signal
import time
import struct
from enum import Enum
from functools import partial
import serial
import RPi.GPIO as GPIO

####################################################################################################
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

####################################################################################################
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

####################################################################################################
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

####################################################################################################
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
lastEvent = 'NOTHING'

# Suivi de l'état général
class UI_State(Enum):
    START_DRAW = 0
    START_WAIT = 1
    BOOK_DRAW = 2
    BOOK_WAIT = 3
    BOOK_PREVIOUSPAGE = 4
    BOOK_NEXTPAGE = 5
    DEMO = 6

# Callback
def shortLongCallback(channel):
    global lastEvent

    misses = 0
    for i in range(10):
        if GPIO.input(channel) == 1:
            misses += 1
            
        if misses >= 2:
            # Short
            lastEvent = 'S' + str(channel)
            return
        else:
            time.sleep(0.1)

    # Long
    lastEvent = 'L' + str(channel)

GPIO.add_event_detect(backBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)
GPIO.add_event_detect(fwdBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)
GPIO.add_event_detect(goBTN_GPIO, GPIO.FALLING, callback=shortLongCallback, bouncetime=1500)

eventShortBack = 'S' + str(backBTN_GPIO)
eventShortFwd  = 'S' + str(fwdBTN_GPIO)
eventShortGo   = 'S' + str(goBTN_GPIO)
eventLongBack  = 'L' + str(backBTN_GPIO)
eventLongFwd   = 'L' + str(fwdBTN_GPIO)
eventLongGo    = 'L' + str(goBTN_GPIO)

# Traitement des événements
def reactToLastEvent(callbackNothing   = lambda : None, 
                     callbackShortBack = lambda : None, 
                     callbackShortFwd  = lambda : None, 
                     callbackShortGo   = lambda : None,
                     callbackLongBack  = lambda : None,
                     callbackLongFwd   = lambda : None,
                     callbackLongGo    = lambda : None):
    global lastEvent
    reactTo = lastEvent

    if reactTo == 'NOTHING':
        callbackNothing()
    elif reactTo == eventShortBack:
        callbackShortBack()
    elif reactTo == eventShortFwd:
        callbackShortFwd()
    elif reactTo == eventShortGo:
        callbackShortGo()
    elif reactTo == eventLongBack:
        callbackLongBack()
    elif reactTo == eventLongFwd:
        callbackLongFwd()
    elif reactTo == eventLongGo:
        callbackLongGo()
    else:
        raise ValueError('Evenement non reconnu')

    lastEvent = 'NOTHING'

    return reactTo

# Register le CTRL+C pour "protéger" les GPIOs à la sortie du programme
def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

####################################################################################################
# State
uiState = UI_State.START_DRAW
demoImageIndex = 0
demoCounter = 0
### Livre
# Ouvrir
lines = []
with open('/home/emile/Verne_Vingtmillelieuessouslesmers.txt') as book:
    lines = [line for line in book]

# Nettoyer lignes
def sanitize(line):
    lineNoWhitespace = line.split()
    lineSimpleWhitespace = ' '.join(lineNoWhitespace)
    
    return lineSimpleWhitespace

sanlines = [ sanitize(line) for line in lines ]

# "Reflow" pour cadrer
reflowedBook = []

lenDisplay = 60

for line in sanlines:
    lenLine = len(line)
    
    if len(line) < lenDisplay:
        reflowedBook.append(line)
    else:
        sublines = [ line[i:i+lenDisplay] for i in range(0, lenLine, lenDisplay) ]
        for subline in sublines:
            reflowedBook.append(subline)
# Le livre est maintenant dans "reflowedBook", une liste de ligne cadrée sur écran EINK

####################################################################################################
# Fonctions appelées
def drawStart():
    wakeup()
    clear()
    setFontSize(3)
    drawText(150, 50, "Prototype de livre")
    drawText(230, 120, "electronique")
    drawCircle(250, 300, 30)
    drawCircle(390, 375, 30)
    drawCircle(250, 450, 30)
    setFontSize(1)
    drawText(300, 285, "Livre")
    drawText(440, 360, "Demo images")
    drawText(300, 435, "Eteindre (Tenir)")
    refresh()
    sleep()

def changeUIState(state):
    global uiState
    uiState = state

def goToStartDraw():
    global demoImageIndex
    demoImageIndex = 0
    global demoCounter
    demoCounter = 0
    changeUIState(UI_State.START_DRAW)

# Affect screen with IMAGE
images = ['MAIS.BMP', 'KID.BMP', 'FIN23.BMP', 'L1984.BMP', 'LABO.BMP', 'LIVRES.BMP', 'LOGOS.BMP', 'MONTR.BMP', 'PIC4.BMP', 'TERRE.BMP']
def wakeUpandUpdate(index):
    wakeup()
    clear()
    displayImage(0, 0, images[index])
    refresh()
    sleep()

def drawBookPage(startPosition):
    wakeup()
    clear()

    for i in range(0, 14):
        drawText(20, 20 + i * 40, reflowedBook[startPosition + i])

    refresh()
    sleep()

def configSD():
    if not setStorageArea("SD"):
        print("Couldn't set storage area")
        sys.exit()

def shutdownWithImage():
    wakeUpandUpdate(5)
    os.system('shutdown 0')

####################################################################################################
# Programme principal

# Config initiale
wakeup()
configSD()

# Boucle maître
while True:
    match uiState:
        case UI_State.START_DRAW:
            drawStart()
            changeUIState(UI_State.START_WAIT)

        case UI_State.START_WAIT:
            reactToLastEvent(callbackShortBack = partial(changeUIState, UI_State.BOOK_DRAW), 
                             callbackShortFwd  = partial(changeUIState, UI_State.DEMO), 
                             callbackLongGo    = shutdownWithImage)

        case UI_State.BOOK_DRAW:
            positionInBook = 0
            with open('/home/emile/bookPosition', 'r') as bookPositionFile:
                positionInBook = int(bookPositionFile.read().split()[0])

            drawBookPage(positionInBook)
            changeUIState(UI_State.BOOK_WAIT)

        case UI_State.BOOK_WAIT:
            reactToLastEvent(callbackShortBack = partial(changeUIState, UI_State.BOOK_PREVIOUSPAGE), 
                             callbackShortFwd  = partial(changeUIState, UI_State.BOOK_NEXTPAGE), 
                             callbackLongGo    = goToStartDraw)

        case UI_State.BOOK_PREVIOUSPAGE:
            positionInBook = 0
            with open('/home/emile/bookPosition', 'r') as bookPositionFile:
                positionInBook = int(bookPositionFile.read().split()[0])

            if positionInBook < 14:
                positionInBook = 0
            else:
                positionInBook -= 14

            with open('/home/emile/bookPosition', 'w') as bookPositionFile:
                bookPositionFile.write(str(positionInBook))

            changeUIState(UI_State.BOOK_DRAW)

        case UI_State.BOOK_NEXTPAGE:
            positionInBook = 0
            with open('/home/emile/bookPosition', 'r') as bookPositionFile:
                positionInBook = int(bookPositionFile.read().split()[0])

            if positionInBook + 14 < len(reflowedBook):
                positionInBook += 14
            else:
                pass

            with open('/home/emile/bookPosition', 'w') as bookPositionFile:
                bookPositionFile.write(str(positionInBook))

            changeUIState(UI_State.BOOK_DRAW)

        case UI_State.DEMO:
            demoCounter += 1

            if demoCounter == 1:
                wakeUpandUpdate(demoImageIndex)
            elif demoCounter == 40:
                demoCounter = 0

                if demoImageIndex == len(images) - 1:
                    demoImageIndex = 0
                else:
                    demoImageIndex += 1

            reactToLastEvent(callbackLongGo = goToStartDraw)

    time.sleep(0.250)
        
