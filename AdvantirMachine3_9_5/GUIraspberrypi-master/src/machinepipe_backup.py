import os
import errno
import time
import RPi.GPIO as GPIO
from ds18b20 import DS18B20 # github rgbkrk/ds18b20
import checksensor as cs
import firstTimeSetup as fts
import ads1256
import math
import serial
import numpy as np

ser = serial.Serial('/dev/ttyACM0')


#-----------PIPE setup---------------

QR2MA_FIFO = 'pipe_from_QR_to_MA'
MA2UI_FIFO = 'pipe_from_MA_to_UI'
UI2MA_FIFO = 'pipe_from_UI_to_MA'
os.system("xset s reset")
os.system("xset s off")

try:
    os.mkfifo(QR2MA_FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

try:
    os.mkfifo(MA2UI_FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

try:
    os.mkfifo(UI2MA_FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

QR2MA_FIFOOpenRead= open(QR2MA_FIFO, 'r', buffering=1)
QR2MA_FIFOOpenRead.read()
print "QR2MA_pipeopened_read"
UI2MA_FIFOOpenRead= open(UI2MA_FIFO, 'r', buffering= 1)
UI2MA_FIFOOpenRead.read()
print "UI2MA_pipeopened_read"



MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
print "MA2UI_pipeopened_write"
os.close(MA2UI_FIFOOpenWrite)

#------------------------------------


menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""

max_motorspeed=1000 # stepper motor mximum speed in rpm


MotorAmp=AugerDownForce=AugerTorque=1

DoorLockpin=17
CapsuleInPin=25

VtclmotorUpPin=24
VtclmotorDownPin=23

DoorClosepin=5#16 spoil
AugerUpLimitPin=20
AugerDownLimitPin=21
Auger2ndLimitPin=12 #27 ori

#rotateMotorCWpin=27
#rotateMotorACWpin=17
#rotateMotorPWMpin=22

QRscannerTrigerpin=06

buzzerpin=22 #22
IRcapdetectPin=12# 12 ori

i2cpin=2, 3
uart=14,15
spi=7,8,9,10,11


GPIO.setmode(GPIO.BCM)
GPIO.setup(DoorLockpin, GPIO.OUT)
GPIO.setup(buzzerpin, GPIO.OUT)
GPIO.setup(VtclmotorUpPin, GPIO.OUT)
GPIO.setup(VtclmotorDownPin, GPIO.OUT)

# GPIO.setup(rotateMotorCWpin, GPIO.OUT)
# GPIO.setup(rotateMotorACWpin, GPIO.OUT)
# GPIO.setup(rotateMotorPWMpin, GPIO.OUT)


# GPIO.setup(EncoderPin, GPIO.IN)
GPIO.setup(QRscannerTrigerpin, GPIO.OUT)

GPIO.output(VtclmotorUpPin,0)
GPIO.output(VtclmotorDownPin,0)

GPIO.output(QRscannerTrigerpin,1) #release barcode scanner trigger



# pwmRotateMotorSpeed=GPIO.PWM(rotateMotorPWMpin, 1000)
# pwmRotateMotorSpeed.start(0)
# #set motor direction
# GPIO.output(rotateMotorCWpin,1)
# GPIO.output(rotateMotorACWpin,0)
screenstate=True

cs1=cs.sensing(DoorClosepin,CapsuleInPin,AugerUpLimitPin,Auger2ndLimitPin,AugerDownLimitPin,IRcapdetectPin, GPIO)
ads1256.start("64","30000")

def doorlock(lock): # lock =1  unlock =0
    if lock:
        GPIO.output(DoorLockpin, 0)
    else:
        GPIO.output(DoorLockpin, 1)

def motorSpeedControl(rpm):
    #rpm to frequency
    val= (rpm*1600*3)/60
    towrite = str(val) + "\n"
    ser.write((towrite).encode('ascii'))
def motorAugerInOut(deg):
    val=deg*3*1600/(360)
    towrite = "r"+str(val) + "\n"
    ser.write((towrite).encode('ascii'))
def motorStop():
    towrite = "stop" + "\n"
    ser.write((towrite).encode('ascii'))
def motorReverse(deg):
    val=deg*3*1600/(360)
    towrite = "k"+str(val) + "\n"
    ser.write((towrite).encode('ascii'))

def AugerEngage():
    GPIO.output(VtclmotorDownPin,1)
#    pwmRotateMotorSpeed.ChangeDutyCycle(0.005)
    motorSpeedControl(4)
    while not cs1.checkAugerDown():
        pass
        # spin slow

    motorSpeedControl(0)
        #break
   # pwmRotateMotorSpeed.ChangeDutyCycle(0)
    GPIO.output(VtclmotorDownPin,0)
    time.sleep(1)


def AugerInOut():
    print "Auger in , Auger Out"
    GPIO.output(VtclmotorUpPin,1) # plateform moving up
    while (not cs1.checkAuger2nd() and not cs1.checkAugerUp()): # until hit 2nd high proximity
        pass
    GPIO.output(VtclmotorUpPin, 0)  # plateform moving up
    motorAugerInOut(60) ## perform turn 45 degree and return 45 degree
    time.sleep(2)
    GPIO.output(VtclmotorDownPin, 1) # plateform moving down
    while not cs1.checkAugerDown(): # until hit down limit
        pass
    GPIO.output(VtclmotorDownPin, 0)  # plateform moving down

def AugerDisengage():
    GPIO.output(VtclmotorUpPin,1)
    while not cs1.checkAugerUp():
        pass

    GPIO.output(VtclmotorUpPin,0)
    return

def buzzerTone(tone):
    if tone==0:
        GPIO.output(buzzerpin, 0)
    if tone==1:
        GPIO.output(buzzerpin, 1)
        time.sleep(0.1)
        GPIO.output(buzzerpin, 0)
        time.sleep(0.1)
        GPIO.output(buzzerpin, 1)
        time.sleep(0.1)
        GPIO.output(buzzerpin, 0)
        time.sleep(0.3)

def motorSpinBlend(soft):
    print "motor process start"
    # if readMotorCurrent:h
    #     pass
    # if readCapsuleDownForce() + readCapsuleSpinForce()>float(soft):
    #     pass
    print "Auger in auger out"
    AugerInOut()
    ads1256.start("64", "30000")
    motorReverse(20)
    time.sleep(0.5)
    zeroRawReading=0
    zerocount=0
    prevalue1=0
    while zerocount<1000:
        rawindependent = ads1256.read_channel(0)
        if rawindependent==0 : continue
        if abs(rawindependent-prevalue1)>200:
            prevalue1=rawindependent
            record=False

        if record==False and prevalue1!=rawindependent and  abs(rawindependent-prevalue1)<200:
            record = True

        if  record:
            if rawindependent < -500 and rawindependent>-750:
                zeroRawReading += rawindependent
                zerocount+=1
    zeroRawReading = zeroRawReading/1000
    #arrayreading=np.array([])
    #for i in range(200):
    #    arrayreading=np.append(arrayreading, np.array([ads1256.read_channel(0)]))
    #zeroRawReading=np.median(arrayreading)
    print "    -pulse process, zeroing:", zeroRawReading
    motorspeed=0
    arrayReading=[]
    timestart=time.time()
    newtonMeter=0

    file1 = open("Mydata.csv", "a")
    file1.write("time , torque, zerovalue \n ")
    pretime = time.time()
    prevalue1 =zeroRawReading
    prevalue2 =0
    record=True
    while 1:
        rawindependent = ads1256.read_channel(0)
        if rawindependent>3000 or rawindependent==0 or rawindependent<-700: continue
        if abs(rawindependent-prevalue1)>300:
            prevalue1=rawindependent
            record=False

        if record==False and prevalue1!=rawindependent and  abs(rawindependent-prevalue1)<300:
            record = True

        if  record:
            prevalue1=rawindependent
            arrayReading.append(rawindependent)
            if len(arrayReading) > 500:
                del arrayReading[0]
            averageRawReading = float(sum(arrayReading)) / len(arrayReading)
            newtonMeter = 2 * 0.0021288 * (averageRawReading - zeroRawReading)  # +1.0173
            print
            "torque: ", newtonMeter, averageRawReading, zeroRawReading
            line = str(time.time() - timestart) + "," + str(newtonMeter) + "," + str(zeroRawReading) + "," + str(
                rawindependent) + "\n"
            file1.write(line)



        if motorspeed < max_motorspeed :
            if pretime+0.1<time.time():
                motorspeed += 10
                motorSpeedControl(motorspeed)
                pretime=time.time()
               # time.sleep(0.1) # motor ramping up delay time



        else :



            if newtonMeter<7 or timestart + 15 < time.time(): # current limit Nm and max blend duration
                motorSpeedControl(0)
                break

    file1.close()


    # for i in range(3): # pulse motor with full power range (1-100)
    #     # pwmRotateMotorSpeed.ChangeDutyCycle(85)
    #     time.sleep(3)
    #     # pwmRotateMotorSpeed.ChangeDutyCycle(0)
    #     time.sleep(1.5)
    # print "    -incresing process"
    # for spd in range(85): # increasing power motor d
    #     # pwmRotateMotorSpeed.ChangeDutyCycle(spd)
    #     time.sleep(0.05)
    #
    # time.sleep(5)
    # pwmRotateMotorSpeed.ChangeDutyCycle(0)

def motorSpinDispense():
    print "dispence start"
    motorspeed=0
    while 1:
        motorspeed+=10
        if motorspeed < max_motorspeed:
            motorSpeedControl(motorspeed)
            time.sleep(0.2) #motor ramping up delay
        else:
            break

    time.sleep(18) # time for dispence
    motorSpeedControl(0)
    # pwmRotateMotorSpeed.ChangeDutyCycle(0)

def MA2UI_pipe_write(input):
    MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
    os.write(MA2UI_FIFOOpenWrite, input)
    os.close(MA2UI_FIFOOpenWrite)

def selectscreen(Scn):
    texttosend = "/SCN:"+Scn+"/"
    pipeout = os.open(MA2UI_FIFO, os.O_WRONLY)
    os.write(pipeout, texttosend)
    os.close(pipeout)
    print Scn," send from MA"

def str2pair(st):
    pairlist = list()
    while True:
        startslash = st.find("/")
        center = st.find(":")
        if center < 0 or startslash < 0:
            break
        firststr = st[startslash + 1: center]
        duplcatedslash=firststr.find("/")
        if duplcatedslash>-1:
            firststr=firststr[duplcatedslash+1:]
        st = st[center:]
        center = st.find(":")
        endslash = st.find("/")
        secondstr = st[center + 1: endslash]
        st = st[endslash:]
        pair = (firststr, secondstr)
        pairlist.append(pair)
    pairlist = dict(pairlist)
    return pairlist

def pair2str(pairlist):
    str=""
    for p in pairlist:
        str=str+"/"+p+":"+pairlist[p]
    str=str+"/"
    return str

def screenOff():
    global screenstate
    if screenstate:
        os.system("xset s activate")
        screenstate=False
def screenOn():
    global screenstate
    if not screenstate:
        os.system("xset s reset")
        screenstate = True
def insertScnFun():
    global state
    selectscreen('insertScn')
    doorlock(False)
    AugerDisengage()

    print"   -platform reach up"
    timestart = time.time()
    while True:
        if not cs1.checkDoorClose():
            screenOn()
            print "   -door open "
            #if capsule and door close detected
            break
        if timestart + 30 < time.time() :
            screenOff()
    state = 'doorcloseScnFun'


def doorcloseScnFun():
    global state
    selectscreen('doorcloseScn')
    timestart = time.time()
    while True:

        if cs1.checkDoorClose():
            print "   -doorclose"
            #if capsule and door close detected
            break
        if timestart+30<time.time():
            buzzerTone(0)
    buzzerTone(0)
    if cs1.checkCapsuleIn():
        state = 'identifyScnFun'
    else:
        state = 'insertScnFun'

def identifyScnFun():
    global state
    selectscreen('identifyScn')
    #servo lock
    #barcode scanner scan capsule
    timeout=False

    timestart=time.time()
    timepass=time.time()

    global menuBRAND, menuTYPE, menuSOFT, menuFLAVOR
    QR_piperead = QR2MA_FIFOOpenRead.read()
    Qrtrigerstate=False

    while True:

        QR_piperead=QR2MA_FIFOOpenRead.read()

        if len(QR_piperead)>1:
            print "QR2MA:", QR_piperead
            st= QR_piperead

            pairlist = str2pair(st)
            #filter barcode
            if "BRAND" in pairlist:
                menuBRAND = pairlist["BRAND"]

            if "TYPE" in pairlist:
                menuTYPE = pairlist["TYPE"]

            if "SOFT" in pairlist:
                menuSOFT = pairlist["SOFT"]
            if "SOFTNESS" in pairlist:
                menuSOFT = pairlist["SOFTNESS"]

            if "FLAVOR" in pairlist:
                if len(pairlist['FLAVOR'])>0 : #barcode scan success
                    MA2UI_pipe_write(QR_piperead)
                    GPIO.output(QRscannerTrigerpin, 1)

                    state = 'recognizedScnFun'
                    break

        if (time.time()-timestart)>10:
            state = 'errorScnFun1'
            break

        if (time.time()-timepass)>1:
            timepass = time.time()
            GPIO.output(QRscannerTrigerpin, Qrtrigerstate)
            Qrtrigerstate = not Qrtrigerstate
        if cs1.checkTemperature()>29:
            state = 'errorScnFun2'
            break

def errorScnFun1(): ## cant recognize QR
    global state
    selectscreen('errorScn1')
    time.sleep(3)
    state ='mainmenuScnFun'
def errorScnFun2(): ## temperature too high
    global state
    selectscreen('errorScn2')
    time.sleep(3)
    state = 'removeScnFun'
def errorScnFun3(): ## no selection and time out
    global state
    selectscreen('errorScn3')
    time.sleep(3)
    state = 'removeScnFun'

def mainmenuScnFun():
    global state
    selectscreen('mainmenuScn')
    UI_piperead = UI2MA_FIFOOpenRead.read() #to clear the pipe if there is old input
    timestart = time.time()

    global menuBRAND,menuTYPE,menuSOFT,menuFLAVOR
    while 1:
        UI_piperead=UI2MA_FIFOOpenRead.read()

        if len(UI_piperead)>1:
            print "UI2MA:", UI_piperead
            st= UI_piperead

            pairlist_UI = str2pair(st)
            #filter barcode
            if "BRAND" in pairlist_UI:
                menuBRAND = pairlist_UI["BRAND"]

            if "TYPE" in pairlist_UI:
                menuTYPE = pairlist_UI["TYPE"]

            if "SOFT" in pairlist_UI:
                menuSOFT = pairlist_UI["SOFT"]

            if "FLAVOR" in pairlist_UI:
                menuFLAVOR = pairlist_UI["FLAVOR"]
                if len(pairlist_UI['FLAVOR'])>0: #barcode scan success
                    state = 'blendingScnFun'
                    break

        if (time.time()-timestart)>120: #if no menu input within 2 min then reset
            state = 'errorScnFun3'
            break

        if not cs1.checkDoorClose():
            state = 'doorcloseScnFun'
            break

        if cs1.checkTemperature()>29:
            state = 'errorScnFun2'
            break
        #wait for input from PIPE

def recognizedScnFun():
    global state
    selectscreen('recognizedScn')
    #lock the door
    timestart=time.time()
    while 1:
        UI_piperead = UI2MA_FIFOOpenRead.read()
        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI = str2pair(st)
            if "TOUCH" in pairlist_UI  :
                doorlock(True)
                state= 'blendingScnFun'
                break
        if (time.time()-timestart)>5:
            doorlock(True)
            state = 'blendingScnFun'
            break
        if not cs1.checkDoorClose():
            state = 'doorcloseScnFun'
            break

        if cs1.checkTemperature()>29:
            state = 'errorScnFun2'
            break



def blendingScnFun():
    global state
    selectscreen('blendingScn')
    AugerEngage()

    motorSpinBlend(menuSOFT);
    state = 'readyScnFun'
    # motor spin till icecreame soft

def readyScnFun():
    global state
    selectscreen('readyScn')

    while True:
        buzzerTone(1)
        UI_piperead = UI2MA_FIFOOpenRead.read()

        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI = str2pair(st)
            if "TOUCH" in pairlist_UI and not cs1.checkCap() :
                state= 'dispensingScnFun'
                break
        if cs1.checkTemperature()>29:
            state = 'errorScnFun2'
            break

def dispensingScnFun():
    global state
    selectscreen('dispensingScn')
    motorSpinDispense();
    time.sleep(5)
    #motor spin for a time period to blend out icecream
    state = 'smileyScnFun'


def smileyScnFun():
    global state
    selectscreen('smileyScn')
    AugerDisengage()
    doorlock(False)
    timestart=time.time()
    while True:
        buzzerTone(1)
        UI_piperead = UI2MA_FIFOOpenRead.read()

        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI = str2pair(st)
            if "TOUCH" in pairlist_UI :
                time.sleep(1)
                break
        if (time.time() - timestart) > 5:
            break

    state = 'removeScnFun'

def removeScnFun():
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
    doorlock(False)
    timestart = time.time()
    while cs1.checkCapsuleIn():
        if (time.time() - timestart) > 5:
            buzzerTone(3)
    state='insertScnFun'

dispatch = {
    'insertScnFun': insertScnFun,
    'doorcloseScnFun': doorcloseScnFun,
    'identifyScnFun': identifyScnFun,
    'mainmenuScnFun': mainmenuScnFun,
    'readyScnFun':readyScnFun,
    'blendingScnFun': blendingScnFun,
    'recognizedScnFun': recognizedScnFun,
    'dispensingScnFun': dispensingScnFun,
    'removeScnFun':removeScnFun,
    'smileyScnFun':smileyScnFun,

    'errorScnFun1': errorScnFun1,
    'errorScnFun2': errorScnFun2,
    'errorScnFun3': errorScnFun3,

}

state="removeScnFun"

time.sleep(10)


fts.fisrttime_setup()

print "begin machine"

while True:

    dispatch[state]() ##state machine

