import os
import sys
sys.path.insert(1, "/home/pi/GUIraspberrypi/src")

import errno
import time
import RPi.GPIO as GPIO
#from ds18b20 import DS18B20 # github rgbkrk/ds18b20
import checksensor as cs
import firstTimeSetup as fts
import ads1256
from ds18b20_temperature_setup import ds18b20_temperature_setup
import math
import serial
import numpy as np
from pairlistdata import pairflavor_force,pairflavor_dispencetime,flavor_params
from printwtime import printtime
import io_param 
import subprocess
import shlex
import json
from csv_reader import find_UPC_from_csv
#from AngleOMeter import x_y_value as anglemeter
from git_pull_check import get_git_headercode
import configparser

config = configparser.ConfigParser()
config.read('/home/pi/swirlgo_machine.conf')
machine_profile=config["machine-config"]
git_start_headercode=get_git_headercode()


# try :
#     print "used udev rules"
#     ser = serial.Serial('/dev/motordrive')
# except:
#     try :
#         print "used ttyACM1"
#         ser = serial.Serial('/dev/ttyACM1')
#     except:
#         print "used ttyACM0"
#         ser = serial.Serial('/dev/ttyACM0')

motordevlist = ["motordrive",
                "ttyACM0", 
		        "ttyACM1", 
		        "ttyUSB0",
                "ttyUSB1"]
motordevroll=0

#----------motor temperature setup----------
motor_temperature=ds18b20_temperature_setup()
    
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
print( "QR2MA_pipeopened_read")

UI2MA_FIFOOpenRead= open(UI2MA_FIFO, 'r', buffering= 1)
UI2MA_FIFOOpenRead.read()
print( "UI2MA_pipeopened_read")

MA2UI_FIFOOpenWrite = os.open(MA2UI_FIFO, os.O_WRONLY)
print( "MA2UI_pipeopened_write")
os.close(MA2UI_FIFOOpenWrite)

#------------------------------------

currentScn="insertScn"
menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""
menuUPC=""

max_motorspeed=1000 # stepper motor mximum speed in rpm
maxmotorStopTemperature=60
minmotorstartTemperature=55
coolingMotor=False
MotorAmp=AugerDownForce=AugerTorque=1

DoorLockpin=io_param.DoorLockpin
CapsuleInPin=io_param.CapsuleInPin #for PCB IR capsule GP12

VtclmotorUpPin=io_param.VtclmotorUpPin
VtclmotorDownPin=io_param.VtclmotorDownPin

DoorClosepin=io_param.DoorClosepin #16 spoil #for PCB sw4 GP16
AugerUpLimitPin=io_param.AugerUpLimitPin  #for PCB sw2 GP20
AugerDownLimitPin=io_param.AugerDownLimitPin #for PCB sw3 GP21
Auger2ndLimitPin=io_param.Auger2ndLimitPin #27 ori  #for PCB IR shaft GP5

#rotateMotorCWpin=27
#rotateMotorACWpin=17
#rotateMotorPWMpin=22

QRscannerTrigerpin=io_param.QRscannerTrigerpin

buzzerpin=io_param.buzzerpin #22
IRcapdetectPin=io_param.IRcapdetectPin # for PCB sw1 GP25 (no more in use )

i2cpin=2, 3
uart=14,15
spi=7,8,9,10,11


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
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
loaded_csv={}
UPCInCsv=False

cs1=cs.sensing(DoorClosepin,CapsuleInPin,AugerUpLimitPin,Auger2ndLimitPin,AugerDownLimitPin,IRcapdetectPin, GPIO)

def connectMotorController():
    global ser,motordevroll
    print "finding motor driver"
    while True:
        connectlink='/dev/'+motordevlist[motordevroll]
        try:
            ser = serial.Serial(connectlink)
            break
        except:
            motordevroll+=1
            motordevroll=motordevroll%len(motordevlist)
            if motordevroll==0:
                restart_USB_LAN_power()

def offsetAngle():
    # offsetsucceed=True
    # try:
    #     for d in range(20):
    #         x, y=anglemeter()
    #         sum_x+=x
    #         sum_y+=y
    # except :
    #     sum_x=0
    #     sum_y=0
    # angleoffsetX=sum_x/20.00
    # angleoffsetY=sum_y/20.00
    # return angleoffsetX,angleoffsetY
    return 0,0
def AngletiltFlag(angleoffsetX, max_angle):
    try:
        x, y=anglemeter()
        measure_x=min(abs(x-angleoffsetX), 360-abs(x-angleoffsetX))

        return measure_x<max_angle
    except:
        print "Gyro Problem"
        return True

def doorlock(lock): # lock =1  unlock =0
    if lock:
        GPIO.output(DoorLockpin, 0)
    else:
        GPIO.output(DoorLockpin, 1)

def restart_USB_LAN_power():
    os.system("sudo sh -c 'echo 1-1 > /sys/bus/usb/drivers/usb/unbind'")
    print "off usb"
    time.sleep(2)

    os.system("sudo sh -c 'echo 1-1 > /sys/bus/usb/drivers/usb/bind'")
    print "on usb"
    time.sleep(2)
    

def write2serial(towrite):
    global ser
    try:
        ser.write((towrite).encode('ascii'))
    except:
        while True:
            try:
                connectMotorController()
                time.sleep(1)
                ser.write((towrite).encode('ascii'))
                break
            except:
                pass
        # loopRetryMotor=True
        # numberofrestart=0
        # while (loopRetryMotor):
        #     loopRetryMotor=False
        #     try:
        #         print( "faulty serial try initialize again motordrive")
        #         ser = serial.Serial('/dev/motordrive')
        #         time.sleep(1)
        #         ser.write((towrite).encode('ascii'))
        #     except:
                
        #         try:
        #             print( "faulty serial try initialize again ttyACM0")
        #             ser = serial.Serial('/dev/ttyACM0')
        #             time.sleep(1)
        #             ser.write((towrite).encode('ascii'))
        #         except:
        #             try:
        #                 print( "faulty serial try initialize again ttyACM1")
        #                 ser = serial.Serial('/dev/ttyACM1')
        #                 time.sleep(1)
        #                 ser.write((towrite).encode('ascii'))
        #             except:
        #                 time.sleep(1)
        #                 loopRetryMotor=True
        #                 numberofrestart+=1
        #                 if numberofrestart ==2 or numberofrestart%20==0:
        #                     restart_USB_LAN_power()
                        
def motorSpeedControl(rpm):
    #rpm to frequency
    if (rpm==0):
        write2serial('s')
    else:
        val= (rpm*1600*3)/60
        towrite = str(val) + "\n"
        write2serial(towrite)


def motorAccNSpeedControl(rpmps,rpm ):
    #rpm to frequency
    reachspeed= (rpm*1600*3)/60
    acc= (rpmps*1600*3*2)/60
    towrite = "a"+str(acc) +","+str(reachspeed) +"\n"
    print (towrite)
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
#    GPIO.output(VtclmotorDownPin,1)

 #   time.sleep(0.7)
 #   GPIO.output(VtclmotorDownPin, 0)
    motorSpeedControl(8)
    time.sleep(1.25)
 #   motorSpeedControl(0)
    #time.sleep(1)
    GPIO.output(VtclmotorDownPin, 1)
    while not cs1.checkAugerDown():
        if not cs1.checkDoorClose():
            GPIO.output(VtclmotorDownPin, 0)
            return False
        else:
            GPIO.output(VtclmotorDownPin, 1)

        # spin slow

        #break
   # pwmRotateMotorSpeed.ChangeDutyCycle(0)
    motorSpeedControl(0)
    GPIO.output(VtclmotorDownPin,0)
    time.sleep(1)
    return True


def AugerInOut():
    print("Auger in , Auger Out")
    GPIO.output(VtclmotorUpPin,1) # plateform moving up
    timers=time.time()
    while (not cs1.checkAuger2nd() and not cs1.checkAugerUp()): # until hit 2nd high proximity
        if int(time.time()-timers)%4 ==3 :
            GPIO.output(VtclmotorUpPin,1)
    GPIO.output(VtclmotorUpPin, 0)  # plateform moving up
    #motorAugerInOut(60) ## perform turn 45 degree and return 45 degree
    time.sleep(2)
    GPIO.output(VtclmotorDownPin, 1) # plateform moving down
    timers=time.time()
    while not cs1.checkAugerDown(): # until hit down limit
        if int(time.time()-timers)%4 ==3 :
            GPIO.output(VtclmotorDownPin,1)
    GPIO.output(VtclmotorDownPin, 0)  # plateform moving down

def AugerDisengage():
    global angleoffsetX,angleoffsetY
    angleoffsetX,angleoffsetY=offsetAngle()
    
    GPIO.output(VtclmotorUpPin,1)
    timers=time.time()
    while not cs1.checkAugerUp() :
        if int(time.time()-timers)%4 ==3 :
            GPIO.output(VtclmotorUpPin,1)

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

def motorSpinBlend():
    print("motor process start")

    print "Auger in auger out"
    #AugerInOut()
    loadcellon = False  # no load cell
    torqueSensor=""
    if loadcellon:
        torqueSensor=torque_ads1256_setup(0.0021288 )
        torqueSensor.init_accumulator()
        file1 = open("Mydata.csv", "a")
        file1.write("time , torque, zerovalue \n ")
        #ads1256.start("64", "30000")
    motorReverse(20)
    time.sleep(0.5)
    print "start blending ...."
    zeroRawReading=0
    if loadcellon:
        zeroRawReading=torqueSensor.try_zeroing( 1000)

    print "    -pulse process, zeroing:", zeroRawReading
    motorspeed=0

    timestart=time.time()
    newtonMeter=0


    pretime = time.time()

    
    if UPCInCsv:
        print "----->",menuFLAVOR ," found flavor in list of set"
    else:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
        
    
    motorSpeedControl(20)
    time.sleep(1)
    motorSpeedControl(0)
    time.sleep(1)

    blend_sequence=json.loads(loaded_csv["BLEND_SEQ"])
    print "[blend_sequence]",blend_sequence
    motorAccNSpeedControl(0,0)
    for param in blend_sequence: # looping every sub param 
        #print "param:",param[0],"," ,param[1],",", param[2]
        motorAccNSpeedControl(param[0],param[1])
        startBlendTime=time.time()
        while (time.time()-startBlendTime)<param[2]:
            if loadcellon:
                averageRawReading=torqueSensor.raw_accumulating_mean()
                newtonMeter=torqueSensor.convert_raw2newtonmeter(averageRawReading)
                
                print "torque: ", newtonMeter, averageRawReading, zeroRawReading
                #write to file for every line
                line = str(time.time() - timestart) + "," + str(newtonMeter) + "," + str(zeroRawReading) + "\n"
                file1.write(line)
            #time.sleep(param[2])
    print "blend ends"


    motorSpeedControl(0)
    time.sleep(1)
    if loadcellon: 
        file1.close()

def motorSpinDispense():
    print("dispence start")

    if UPCInCsv:
        print "----->",menuFLAVOR ," found flavor in list of set"
    else:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
        
    dispence_sequence=json.loads(loaded_csv["DISPENSE_SEQ"])
    print "[dispence_sequence]",dispence_sequence
    motorAccNSpeedControl(0,0)
    for param in dispence_sequence:
        motorAccNSpeedControl(param[0],param[1])
        time.sleep(param[2])
    motorSpeedControl(0)
    extratime=0
    motortemp=motor_temperature.averageTemperature(1)
    print "[MotorTemperature] "+str(motortemp)

    
    
   
'''
def motorSpinDispense():
    print("dispence start")
    motorspeed=0
    #while 1:
    #    motorspeed+=10
    #    if motorspeed <max_motorspeed:
    #        motorSpeedControl(motorspeed)
    #        time.sleep(0.2)
    #    else:
    #        break
    dispense_motorspeed=800
    
    current_motortemp=0
    while 1:
    
        motorspeed+=20 #dispense ramp speed interval
        if motorspeed < dispense_motorspeed:
            motorSpeedControl(motorspeed)
            time.sleep(0.05) #motor ramping up delay
        else:
            motorSpeedControl(800)
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
    motortemp=averageTemperature()
    print "[MotorTemperature] "+str(motortemp)
    try:
        extratime=flavor_params[menuFLAVOR]['dispensetime']
        print "----->",menuFLAVOR ," found flavor in list of set"
    except:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
    time.sleep(9+extratime) # time variable for dispense after ramp up (originally is 20) 30
    motorSpeedControl(0)
    # pwmRotateMotorSpeed.ChangeDutyCycle(0)
'''
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
    global currentScn
    currentScn=Scn
    texttosend = '{"SCN":"'+Scn+'"}'
    # keep looping to wait reply from UI is match screen 
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
                pairlist_UI = jsonOrganizeLoad(st)
                if "SCN" in pairlist_UI:
                    if  pairlist_UI["SCN"]==Scn:
                        screenmatched=True
                        break
        if screenmatched:
            break

    print Scn," send from MA"

def jsonOrganizeLoad(txt):
    txtsplit=txt.replace("}{", "},{")
    txtsplit=txtsplit.replace("} {", "},{")
    txtsplit="["+txtsplit+"]"
    try:
        arraylistfile=json.loads(txtsplit)
        singlelist={}
        for listi in arraylistfile:
            singlelist.update(listi)
        return singlelist
    except:
        print "json load error"
        return {}
'''
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
'''
def screenOff():
    global screenstate
    if screenstate:
        os.system("xset s activate")
        screenstate=False

def screenOn():
    os.system("xset s reset")
    # global screenstate
    # if not screenstate:
    #     os.system("xset s reset")
    #     screenstate = True
def insertScnFun():
    print("state: insertScnFun")
    global state
    selectscreen('insertScn')
   
    AugerDisengage()

    print"   -platform reach up"
    # os.system("xset s on")
    # os.system("xset s 30")
    timestart = time.time()
    while True:

        if git_start_headercode!=get_git_headercode():
            print "rebooting for update"
            time.sleep(2)
            os.system("sudo reboot")
        
        if not cs1.checkDoorClose():
            # os.system("xset s reset")
            # os.system("xset s off")
            if timestart+3<time.time()<timestart+3+15:
                buzzerTone(1)
            if cs1.checkCapsuleIn():
                print "   -door open and capsule insert"
                state = 'doorcloseInsertScnFun'
            #if capsule and door close detected
                break
        else:
            timestart = time.time()
        # if timestart + 30 < time.time() :
        #     print " screen off  "
        #     screenOff()
    buzzerTone(0)
    

    


def doorcloseInsertScnFun():

    print("state: doorcloseInsertScnFun")
    global state
    selectscreen('doorcloseInsertScn')
    AugerDisengage()
    timestart = time.time()
    while True:
        
        if not cs1.checkCapsuleIn():
            state = 'insertScnFun'
            break

        if cs1.checkDoorClose() and cs1.checkCapsuleIn():
            print "   -doorclose"
            #if capsule and door close detected
            state = 'identifyScnFun'
            break
        if timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)
    buzzerTone(0)

        



def identifyScnFun():

    print("state: identifyScnFun")
    global state
    selectscreen('identifyScn')
    #servo lock
    #barcode scanner scan capsule


    timestart=time.time()
    timepass=time.time()

    global menuBRAND, menuTYPE, menuSOFT, menuFLAVOR,menuUPC, coolingMotor,UPCInCsv,loaded_csv,QR2MA_FIFOOpenRead
    menuBRAND=""
    menuTYPE=""
    menuSOFT=""
    menuFLAVOR=""
    menuUPC=""
    loaded_csv={}
    QR_piperead = QR2MA_FIFOOpenRead.read()
    Qrtrigerstate=False
    
    #motortemp=motor_temperature.averageTemperature(20)
    #print "[motorStartTemperature] "+str(motortemp)

    
    # if motortemp > maxmotorStopTemperature :
    #     state = 'errorScnFun2'
    #     return 

    UPCInCsv=False
    while True:

        QR_piperead=QR2MA_FIFOOpenRead.read()

        if len(QR_piperead)>1:
            print "QR2MA:", QR_piperead
            
            pairlist =  jsonOrganizeLoad(QR_piperead)
            if "UPC" in pairlist:
                menuUPC = pairlist["UPC"]

                if len(pairlist['UPC'])>0 : #barcode scan success

                    UPCInCsv,loaded_csv=find_UPC_from_csv(menuUPC)
                    menuBRAND=loaded_csv['BRAND']
                    menuTYPE=loaded_csv['TYPE']
                    menuSOFT=loaded_csv['SOFT']
                    menuFLAVOR=loaded_csv['FLAVOUR']
                    print "get menuFLAVOR",menuFLAVOR

                    MA2UI_pipe_write(json.dumps(loaded_csv))
                    GPIO.output(QRscannerTrigerpin, 1)

                    if UPCInCsv:
                        state = 'recognizedScnFun'
                    else:
                        state = 'blendingScnFun'
                    break

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
            UPCInCsv,loaded_csv=find_UPC_from_csv('DEFAULT')
            menuBRAND=loaded_csv['BRAND']
            menuTYPE=loaded_csv['TYPE']
            menuSOFT=loaded_csv['SOFT']
            menuFLAVOR=loaded_csv['FLAVOUR']
            MA2UI_pipe_write(json.dumps(loaded_csv))
            GPIO.output(QRscannerTrigerpin, 1)
            break

        if (time.time()-timepass)>1:
            print "trigering QR"
            timepass = time.time()
            GPIO.output(QRscannerTrigerpin, Qrtrigerstate)
            Qrtrigerstate = not Qrtrigerstate

        if not cs1.checkDoorClose():
            state = 'doorcloseInsertScnFun'
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
    while True:
        motortemp=motor_temperature.averageTemperature(1)
        print "[motorCoolingTemperature] "+str(motortemp)
        if motortemp< minmotorstartTemperature:
            break
        time.sleep(30)

    state = 'removeScnFun_checkcapsule'

def errorScnFun3(): ## no selection and time out
    global state
    selectscreen('errorScn3')
    time.sleep(3)
    state = 'removeScnFun'

def mainmenuScnFun():
    global state
    print("state: mainmenuScn")
    selectscreen('mainmenuScn')
    UI_piperead = UI2MA_FIFOOpenRead.read() #to clear the pipe if there is old input
    timestart = time.time()

    global menuBRAND,menuTYPE,menuSOFT,menuFLAVOR
    while 1:
        UI_piperead=UI2MA_FIFOOpenRead.read()

        if len(UI_piperead)>1:
            print "UI2MA:", UI_piperead
            st= UI_piperead

            pairlist_UI =  jsonOrganizeLoad(st)
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
            state = 'doorcloseInsertScnFun'
            break

        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break
        #wait for input from PIPE

def recognizedScnFun():

    print("state: recognizedScnFun")
    global state
    selectscreen('recognizedScn')
    #lock the door
    timestart=time.time()
    while 1:
        UI_piperead = UI2MA_FIFOOpenRead.read()
        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI =  jsonOrganizeLoad(st)
            if "TOUCH" in pairlist_UI  :
               
                state= 'blendingScnFun'
                break
        if (time.time()-timestart)>5:
         
            state = 'blendingScnFun'
            break
        if not cs1.checkDoorClose():
            state = 'doorcloseInsertScnFun'
            break

        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break



def blendingScnFun():

    print("state: blendingScnFun")
    global state
    selectscreen('blendingScn')
    if not AugerEngage():
        state='doorcloseInsertScnFun'
        return

    motorSpinBlend()
    state = 'readyScnFun'
    # motor spin till icecreame soft

def readyScnFun():

    print("state: readyScnFun")
    global state
    selectscreen('opencapScn')
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
            pairlist_UI =  jsonOrganizeLoad(st)
            if "TOUCH" in pairlist_UI :
                state= 'dispensingScnFun'
                break
        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break

def dispensingScnFun():

    print("state: dispensingScnFun")
    global state
    selectscreen('dispensingScn')
    motorSpinDispense();
    time.sleep(1)
    AugerDisengage()
    #motor spin for a time period to blend out icecream

    state = 'removeScnFun_checkdoor'


def smileyScnFun():

    print("state: smileyScnFun")
    global state
    selectscreen('smileyScn')
    AugerDisengage()
    capsulecheckremoveflag=False

    timestart=time.time()
    selectedrating=0
    while True:
        #buzzerTone(1)
        UI_piperead = UI2MA_FIFOOpenRead.read()

        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI =  jsonOrganizeLoad(st)
            if "RATE" in pairlist_UI :
                selectedrating=int(pairlist_UI["RATE"])
                time.sleep(1)
                break
        if (time.time() - timestart) > 5 or  (time.time() - timestart) < 0 :
            break
        if not cs1.checkCapsuleIn():
            capsulecheckremoveflag=True
    # state = 'removeScnFun'
    buzzerTone(0)
    print "[Sales] [4] "+menuUPC+ \
         " [5] "+loaded_csv["UPC"]+" [6] "+"A"+ \
         " [7] "+loaded_csv["BRAND"]+" [8] "+loaded_csv['FLAVOUR']+ \
         " [9] "+loaded_csv["BLEND_SEQ"]+"+"+loaded_csv["DISPENSE_SEQ"]+ \
         " [10] "+str(selectedrating)+" [11] "+machine_profile["MID"]+ \
         " [12] "+str(2.50)+" [13] "+str(0.12)+" [14] "+machine_profile["customer_brand"]
    
    if capsulecheckremoveflag:
        state = 'doorcloseRemoveScnFun'
    else:
        state = 'removeScnFun_checkcapsule'

def removeScnFun():

    print("state: removeScnFun")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()

    timestart = time.time()
    while cs1.checkCapsuleIn():
        if timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)
    state='insertScnFun'




def removeScnFun_checkdoor():
    print( "state: removeScnFun_checkdoor")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()
 
    timestart = time.time()
    while cs1.checkDoorClose():
        if timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)
    buzzerTone(0)
    state='smileyScnFun'

def removeScnFun_checkcapsule():

    print("state: removeScnFun_checkcapsule")
    global state
    selectscreen('removeScn')
    #time.sleep(5)
    AugerDisengage()

    timestart = time.time()
    while cs1.checkCapsuleIn():
        if timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)
    buzzerTone(0)
    state='doorcloseRemoveScnFun'



def doorcloseRemoveScnFun():

    print("state: doorcloseRemoveScnFun")
    global state
    selectscreen('doorcloseRemoveScn')
    timestart = time.time()
    while True:

        if cs1.checkDoorClose()  :
            print "   -doorclose"
            #if capsule and door close detected
            state = 'insertScnFun'
            break
        if cs1.checkCapsuleIn():
            print "    -New capsule insert"
            state="doorcloseInsertScnFun"
            break
        
        if timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)
    buzzerTone(0)

def main_coveropen_cb(coverSafetyPin):
    print "inside cover open callback loop"
    timestart = time.time()
    while (time.time()-timestart)<0.2:
        if  not GPIO.input(coverSafetyPin): #if press
            print "false cover safety detection"
            return
    k=0
    print "entering cover open safety freeze"
    passScn=currentScn
    selectscreen('errorScn3')
    # stop all motors
    motorSpeedControl(0)
    GPIO.output(VtclmotorUpPin, 0)  # plateform moving up
    GPIO.output(VtclmotorDownPin, 0)  # plateform moving down
    print "[PauseMA]"
    while True:
    
        if not GPIO.input(coverSafetyPin): #if press
            k=k+1
        else : 
            k=0
        if k>5:
            break
    print "quit cover open callback loop"
    selectscreen(passScn)

def run_command(command, label):
    process = subprocess.Popen(shlex.split(command), bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    while True:
        output = process.stdout.readline()
 
        if output == '' and process.poll() is not None:
            break
        if output :
            print label+output


    rc = process.poll()
    return rc

connectMotorController()
dispatch = {
    'insertScnFun': insertScnFun,
    'doorcloseRemoveScnFun': doorcloseRemoveScnFun,
    'doorcloseInsertScnFun': doorcloseInsertScnFun,
 
    'removeScnFun_checkdoor':removeScnFun_checkdoor,
    'removeScnFun_checkcapsule':removeScnFun_checkcapsule,

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
print("entering ")
state="removeScnFun"
print("entering2 ")
motorSpeedControl(0)
print("entering3 ")
time.sleep(10)
print("entering 4")

# for screen test +++++++++++
# testlistofscreen = ["insertScn", "doorcloseScn", "identifyScn", "recognizedScn", "errorScn1", "errorScn2", "errorScn3",
#                     "blendingScn", "readyScn", "dispensingScn", "smileyScn", "thankyouScn", "mainmenuScn",
#                     "submenuScn", "removeScn", "wifiScn"]
#++++++++++++++++++++++++++++
print("entering first time setup")
fts.fisrttime_setup()

print("begin machine")
if "cover_safety" in  machine_profile: 
    if machine_profile.getboolean("cover_safety"):
        print "cover_safety enable"
        GPIO.add_event_detect(IRcapdetectPin, GPIO.RISING,callback=main_coveropen_cb, bouncetime=10)

while True:
    dispatch[state]()  ##state machine
    run_command("vcgencmd measure_temp", "[CPUtemperature] ")
    run_command("free -h", "[Memory] ")
    # for screen test +++++++++++
    # for i in testlistofscreen:
    #     selectscreen(i)
    #     time.sleep(5)
    # ++++++++++++++++++++++++++++
