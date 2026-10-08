import os
import errno
import time
import RPi.GPIO as GPIO
#from ds18b20 import DS18B20 # github rgbkrk/ds18b20
import checksensor as cs
import firstTimeSetup as fts
import ads1256
import math
import serial
import numpy as np
from pairlistdata import pairflavor_force,pairflavor_dispencetime,flavor_params
from printwtime import printtime


try :
    print "used udev rules"
    ser = serial.Serial('/dev/motordrive')
except:
    try :
        print "used ttyACM1"
        ser = serial.Serial('/dev/ttyACM1')
    except:
        print "used ttyACM0"
        ser = serial.Serial('/dev/ttyACM0')


#-----------PIPE setup---------------

QR2MA_FIFO = 'pipe_from_QR_to_MA'
MA2UI_FIFO = 'pipe_from_MA_to_UI'
UI2MA_FIFO = 'pipe_from_UI_to_MA'
os.system("xset s reset")

os.system("xset s off")
os.system("xset -dpms")
os.system("xset s noblank")
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
printtime( "QR2MA_pipeopened_read")
UI2MA_FIFOOpenRead= open(UI2MA_FIFO, 'r', buffering= 1)
UI2MA_FIFOOpenRead.read()
printtime( "UI2MA_pipeopened_read")



MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
printtime( "MA2UI_pipeopened_write")
os.close(MA2UI_FIFOOpenWrite)

#------------------------------------


menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""

max_motorspeed=1000 # stepper motor mximum speed in rpm


MotorAmp=AugerDownForce=AugerTorque=1

DoorLockpin=17 #for PCB output solenoid
CapsuleInPin=25 #for PCB IR capsule GP12

VtclmotorUpPin=24
VtclmotorDownPin=23

DoorClosepin=5#16 spoil #for PCB sw4 GP16
AugerUpLimitPin=20  #for PCB sw2 GP20
AugerDownLimitPin=21 #for PCB sw3 GP21
Auger2ndLimitPin=12 #27 ori  #for PCB IR shaft GP5

#rotateMotorCWpin=27
#rotateMotorACWpin=17
#rotateMotorPWMpin=22

QRscannerTrigerpin=06

buzzerpin=22 #22
IRcapdetectPin=12 # for PCB sw1 GP25 (no more in use )

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


def doorlock(lock): # lock =1  unlock =0
    if lock:
        GPIO.output(DoorLockpin, 0)
    else:
        GPIO.output(DoorLockpin, 1)

def write2serial(towrite):
    global ser
    try:
        ser.write((towrite).encode('ascii'))
    except:
        try:
            printtime( "faulty serial try initialize again motordrive")
            ser = serial.Serial('/dev/motordrive')
            ser.write((towrite).encode('ascii'))
        except:
            try:
                printtime( "faulty serial try initialize again ttyACM0")
                ser = serial.Serial('/dev/ttyACM0')
                ser.write((towrite).encode('ascii'))
            except:
                printtime( "faulty serial try initialize again ttyACM1")
                ser = serial.Serial('/dev/ttyACM1')
                ser.write((towrite).encode('ascii'))

def motorSpeedControl(rpm):
    #rpm to frequency
    val= (rpm*1600*3)/60
    towrite = str(val) + "\n"
    write2serial(towrite)

def motorAugerInOut(deg):
    val=deg*3*1600/(360)
    towrite = "r"+str(val) + "\n"
    write2serial(towrite)

def motorStop():
    towrite = "stop" + "\n"
    write2serial(towrite)

def motorReverse(deg):
    val=deg*3*1600/(360)
    towrite = "k"+str(val) + "\n"
    write2serial(towrite)


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
    printtime("Auger in , Auger Out")
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
    if tone==2:
        GPIO.output(buzzerpin, 1)
        time.sleep(0.1)
        GPIO.output(buzzerpin, 0)

def motorSpinBlend(soft):
    printtime("motor process start")
    # if readMotorCurrent:h
    #     pass
    # if readCapsuleDownForce() + readCapsuleSpinForce()>float(soft):
    #     pass
    print "Auger in auger out"
    AugerInOut()
    loadcellon = False  # no load cell
    if loadcellon:
        ads1256.start("64", "30000")
    motorReverse(20)
    time.sleep(0.5)
    zeroRawReading=0
    zerocount=0
    prevalue1=0
    print "start blending ...."

    if loadcellon:
        while zerocount<1000:
            rawindependent =  ads1256.read_channel(0)
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
    NmTobeSet=1000
    try:

        NmTobeSet = flavor_params[menuFLAVOR]['blendtime']
        print "----->", menuFLAVOR, " found flavor in list of set"
    except:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"

    motorSpeedControl(20)
    time.sleep(1)
    motorSpeedControl(0)
    time.sleep(0.5)

    while 1:
        if loadcellon:
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
                print "torque: ", newtonMeter, averageRawReading, zeroRawReading
                line = str(time.time() - timestart) + "," + str(newtonMeter) + "," + str(zeroRawReading) + "," + str(
                    rawindependent) + "\n"
                file1.write(line)



        if motorspeed < max_motorspeed:
            if pretime+0.05<time.time():
                motorspeed += 20
                motorSpeedControl(motorspeed)
                pretime=time.time()
               # time.sleep(0.1) # motor ramping up delay time



        else :

       #     if newtonMeter < NmTobeSet or timestart + 8 < time.time():  # current limit Nm or max blend duration
            if newtonMeter<1000 and timestart + 3 < time.time(): # current limit Nm and max blend duration
                motorSpeedControl(0)
                break
    motorSpeedControl(0)
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
    printtime("dispence start")
    motorspeed=0
    #while 1:
    #    motorspeed+=10
    #    if motorspeed <max_motorspeed:
    #        motorSpeedControl(motorspeed)
    #        time.sleep(0.2)
    #    else:
    #        break
    dispense_motorspeed=500
    while 1:
        motorspeed+=20
        if motorspeed < dispense_motorspeed:
            motorSpeedControl(motorspeed)
            time.sleep(0.05) #motor ramping up delay
        else:
            motorSpeedControl(300)
            time.sleep(8)
            while 1:
                motorspeed+=10
                if motorspeed < max_motorspeed:
                    motorSpeedControl(motorspeed)
                    time.sleep(0.1)  # motor ramping up delay
                else:
                    break
            break

    extratime=0
    try:
        extratime=flavor_params[menuFLAVOR]['dispensetime']
        print "----->",menuFLAVOR ," found flavor in list of set"
    except:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
    time.sleep(12+extratime) # time for dispence after ramp up
    motorSpeedControl(0)
    # pwmRotateMotorSpeed.ChangeDutyCycle(0)

def MA2UI_pipe_write(input):
    MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
    os.write(MA2UI_FIFOOpenWrite, input)
    os.close(MA2UI_FIFOOpenWrite)
    time.sleep(0.2)
    MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
    os.write(MA2UI_FIFOOpenWrite, input)
    os.close(MA2UI_FIFOOpenWrite)
#
# def selectscreen(Scn):
#     texttosend = "/SCN:" + Scn + "/"
#     MA2UI_pipe_write(texttosend)

def selectscreen(Scn):
    texttosend = "/SCN:"+Scn+"/"
    while True:
        screenmatched=False
        pipeout = os.open(MA2UI_FIFO, os.O_WRONLY)
        os.write(pipeout, texttosend)
        os.close(pipeout)
        timestart= time.time()
        while timestart+0.2>time.time():
            UI_piperead = UI2MA_FIFOOpenRead.read()
            if len(UI_piperead) > 1:
                print "UI2MA:", UI_piperead
                st = UI_piperead
                pairlist_UI = str2pair(st)
                if "SCN" in pairlist_UI:
                    if  pairlist_UI["SCN"]==Scn:
                        screenmatched=True
                        break
        if screenmatched:
            break

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
    print "decode pairdict:", pairlist
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
# def screenOn():
#     global screenstate
#     if not screenstate:
#         os.system("xset s reset")
#         screenstate = True
def screenOn():
    os.system("xset s reset")
    # global screenstate
    # if not screenstate:
    #     os.system("xset s reset")
    #     screenstate = True
def insertScnFun():
    printtime("state: insertScnFun")
    global state
    selectscreen('insertScn')
    doorlock(False)
    AugerDisengage()

    print"   -platform reach up"
    # os.system("xset s on")
    # os.system("xset s 30")
    while True:
        if not cs1.checkDoorClose():
            # os.system("xset s reset")
            # os.system("xset s off")
            print "   -door open "
            #if capsule and door close detected
            break
        # if timestart + 30 < time.time() :
        #     print " screen off  "
        #     screenOff()


    state = 'doorcloseScnFun'


def doorcloseScnFun():

    printtime("state: doorcloseScnFun")
    global state
    selectscreen('doorcloseScn')
    timestart = time.time()
    while True:

        if cs1.checkDoorClose():
            print "   -doorclose"
            #if capsule and door close detected
            break
        if timestart+10<time.time():
            buzzerTone(1)
    buzzerTone(0)
    if cs1.checkCapsuleIn():
        state = 'identifyScnFun'
    else:
        state = 'insertScnFun'

def identifyScnFun():

    printtime("state: identifyScnFun")
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
                menuFLAVOR = pairlist["FLAVOR"]
                if len(pairlist['FLAVOR'])>0 : #barcode scan success
                    MA2UI_pipe_write(QR_piperead)
                    GPIO.output(QRscannerTrigerpin, 1)

                    state = 'recognizedScnFun'
                    break

        if (time.time()-timestart)>10:
            state = 'blendingScnFun'
            break

        if (time.time()-timepass)>1:
            timepass = time.time()
            GPIO.output(QRscannerTrigerpin, Qrtrigerstate)
            Qrtrigerstate = not Qrtrigerstate

        if not cs1.checkDoorClose():
            state = 'doorcloseScnFun'
            break
        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break

def errorScnFun1(): ## cant recognize QR
    global state
    selectscreen('errorScn1')
    time.sleep(3)
    # state ='mainmenuScnFun'
    state = 'blendingScnFun'
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
    printtime("state: mainmenuScn")
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

        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break
        #wait for input from PIPE

def recognizedScnFun():

    printtime("state: recognizedScnFun")
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

        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break



def blendingScnFun():

    printtime("state: blendingScnFun")
    global state
    selectscreen('blendingScn')
    AugerEngage()

    motorSpinBlend(menuSOFT);
    state = 'readyScnFun'
    # motor spin till icecreame soft

def readyScnFun():

    printtime("state: readyScnFun")
    global state
    selectscreen('readyScn')
    timestart = 0
    while True:

        UI_piperead = UI2MA_FIFOOpenRead.read()
        if (time.time()-timestart)>3:
            buzzerTone(2)
            timestart=time.time()
        else:
            buzzerTone(0)

        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI = str2pair(st)
            if "TOUCH" in pairlist_UI :
                state= 'dispensingScnFun'
                break
        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break

def dispensingScnFun():

    printtime("state: dispensingScnFun")
    global state
    selectscreen('dispensingScn')
    motorSpinDispense();
    time.sleep(1)
    AugerDisengage()
    #motor spin for a time period to blend out icecream

    state = 'removeScnFun_checkdoor'


def smileyScnFun():

    printtime("state: smileyScnFun")
    global state
    selectscreen('smileyScn')
    AugerDisengage()
    capsulecheckremoveflag=False
    doorlock(False)
    timestart=time.time()
    while True:
        #buzzerTone(1)
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
        if not cs1.checkCapsuleIn():
            capsulecheckremoveflag=True
    # state = 'removeScnFun'
    buzzerTone(0)
    if capsulecheckremoveflag:
        state = 'doorcloseScnFun'
    else:
        state = 'removeScnFun_checkcapsule'

def removeScnFun():

    printtime("state: removeScnFun")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
    doorlock(False)
    timestart = time.time()
    while cs1.checkCapsuleIn():
        if (time.time() - timestart) > 5:
            buzzerTone(1)
    state='insertScnFun'


def removeScnFun_complete():

    printtime("state: removeScnFun_complete")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
    doorlock(False)
    timestart = time.time()
    while cs1.checkCapsuleIn():
        if (time.time() - timestart) > 5:
            buzzerTone(1)
    buzzerTone(0)
    state='doorcloseScnFun_complete'


def removeScnFun_checkdoor():
    printtime( "state: removeScnFun_checkdoor")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
    doorlock(False)
    timestart = time.time()
    while cs1.checkDoorClose():
        if (time.time() - timestart) > 5:
            buzzerTone(1)
    buzzerTone(0)
    state='smileyScnFun'

def removeScnFun_checkcapsule():

    printtime("state: removeScnFun_checkcapsule")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
    doorlock(False)
    timestart = time.time()
    while cs1.checkCapsuleIn():
        if (time.time() - timestart) > 5:
            buzzerTone(1)
    buzzerTone(0)
    state='doorcloseScnFun'

def doorcloseScnFun_complete():

    printtime("state: doorcloseScnFun_complete")
    global state
    selectscreen('doorcloseScn')
    timestart = time.time()
    while True:

        if cs1.checkDoorClose():
            print "   -doorclose"
            #if capsule and door close detected
            break
        if timestart+5<time.time():
            buzzerTone(1)
    buzzerTone(0)
    if cs1.checkCapsuleIn():
        state = 'removeScnFun_complete'
    else:
        state='smileyScnFun'


dispatch = {
    'insertScnFun': insertScnFun,
    'doorcloseScnFun': doorcloseScnFun,
    'doorcloseScnFun_complete': doorcloseScnFun_complete,
    'removeScnFun_checkdoor':removeScnFun_checkdoor,
    'removeScnFun_checkcapsule':removeScnFun_checkcapsule,

    'identifyScnFun': identifyScnFun,
    'mainmenuScnFun': mainmenuScnFun,
    'readyScnFun':readyScnFun,
    'blendingScnFun': blendingScnFun,
    'recognizedScnFun': recognizedScnFun,
    'dispensingScnFun': dispensingScnFun,
    'removeScnFun':removeScnFun,
    'removeScnFun_complete':removeScnFun_complete,
    'smileyScnFun':smileyScnFun,

    'errorScnFun1': errorScnFun1,
    'errorScnFun2': errorScnFun2,
    'errorScnFun3': errorScnFun3,

}

state="removeScnFun"
motorSpeedControl(0)
time.sleep(10)

# for screen test +++++++++++
# testlistofscreen = ["insertScn", "doorcloseScn", "identifyScn", "recognizedScn", "errorScn1", "errorScn2", "errorScn3",
#                     "blendingScn", "readyScn", "dispensingScn", "smileyScn", "thankyouScn", "mainmenuScn",
#                     "submenuScn", "removeScn", "wifiScn"]
#++++++++++++++++++++++++++++
fts.fisrttime_setup()

printtime("begin machine")

while True:
    dispatch[state]()  ##state machine

    # for screen test +++++++++++
    # for i in testlistofscreen:
    #     selectscreen(i)
    #     time.sleep(5)
    # ++++++++++++++++++++++++++++