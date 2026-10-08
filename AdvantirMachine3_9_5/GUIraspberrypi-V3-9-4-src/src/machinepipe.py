import os
import sys
import traceback
sys.path.insert(1, "/home/pi/GUIraspberrypi/src")

import errno
import time
import RPi.GPIO as GPIO
#from ds18b20 import DS18B20 # github rgbkrk/ds18b20
import checksensor as cs
import firstTimeSetup as fts
#import ads1256
from ds18b20_temperature_setup import ds18b20_temperature_setup
import math
import serial
import numpy as np
from pairlistdata import pairflavor_force,pairflavor_dispencetime,flavor_params
from printwtime import printtime
import io_param 
import subprocess
import shlex
import signal
import json
from csv_reader import find_UPC_from_csv, find_UPC_n_SOFT_from_csv
#from AngleOMeter import x_y_value as anglemeter
from git_pull_check import get_git_headercode, get_git_headercode_param
import configparser
from Induction_Handler import Induction_Handler
from ESP32Controller import ESP32Controller 
import SharedArray as sa

config = configparser.ConfigParser()
config.read('/home/pi/swirlgo_machine.conf')
machine_profile=config["machine-config"]
git_start_headercode=get_git_headercode()
git_start_headercode_param=get_git_headercode_param()
#----------Share Memory-----------
try:
    shm_ma2ui = sa.attach("shm://sgo-ma-ui")
    print "previous sgo-ma-ui share memory exit,attaching it"
except:
    print "sgo-ma-ui share memory not exit"   
    shm_ma2ui = sa.create('shm://sgo-ma-ui',1, dtype=bool) 

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

currentScn="removeScn"
menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""
menuUPC=""
timerLastTempCheck=0
capsuleTemperature=-10
capsule_min_temp=20
max_motorspeed=1000 # stepper motor mximum speed in rpm
maxmotorStopTemperature=60
minmotorstartTemperature=55
coolingMotor=False
MotorAmp=AugerDownForce=AugerTorque=1

# IRTempTrigPin=io_param.IRTempTrigPin
CapsuleInPin=io_param.CapsuleInPin #for PCB IR capsule GP12

VtclmotorUpPin=io_param.VtclmotorUpPin
VtclmotorDownPin=io_param.VtclmotorDownPin

DoorClosepin=io_param.DoorClosepin #16 spoil #for PCB sw4 GP16
AugerUpLimitPin=io_param.AugerUpLimitPin  #for PCB sw2 GP20
AugerDownLimitPin=io_param.AugerDownLimitPin #for PCB sw3 GP21
# Auger2ndLimitPin=io_param.Auger2ndLimitPin #27 ori  #for PCB IR shaft GP5
InductionPin=io_param.InductionPin
MCUresetPin=io_param.MCUresetPin

#rotateMotorCWpin=27
#rotateMotorACWpin=17
#rotateMotorPWMpin=22

QRscannerTrigerpin=io_param.QRscannerTrigerpin

buzzerpin=io_param.buzzerpin #22
MainCoverClosePin=io_param.MainCoverClosePin # for PCB sw1 GP25 (no more in use )



GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# GPIO.setup(IRTempTrigPin, GPIO.OUT)
GPIO.setup(buzzerpin, GPIO.OUT)

GPIO.setup(VtclmotorUpPin, GPIO.OUT)
GPIO.setup(VtclmotorDownPin, GPIO.OUT)
# GPIO.setup(InductionPin,GPIO.OUT)
GPIO.setup(MCUresetPin, GPIO.OUT)
# GPIO.setup(rotateMotorCWpin, GPIO.OUT)
# GPIO.setup(rotateMotorACWpin, GPIO.OUT)
# GPIO.setup(rotateMotorPWMpin, GPIO.OUT)


# GPIO.setup(EncoderPin, GPIO.IN)
GPIO.setup(QRscannerTrigerpin, GPIO.OUT)




GPIO.output(VtclmotorUpPin,0)
GPIO.output(VtclmotorDownPin,0)
GPIO.output(MCUresetPin,1)
GPIO.output(QRscannerTrigerpin,1) #release barcode scanner trigger


# boardser=serial.Serial(port='/dev/ttyS0',baudrate=9600,timeout=3.0)
# pwmRotateMotorSpeed=GPIO.PWM(rotateMotorPWMpin, 1000)
# pwmRotateMotorSpeed.start(0)
# #set motor direction
# GPIO.output(rotateMotorCWpin,1)
# GPIO.output(rotateMotorACWpin,0)
screenstate=True
loaded_csv={}
UPCInCsv=False

cs1=cs.sensing(DoorClosepin,CapsuleInPin,AugerUpLimitPin,io_param.SpareI1Pin,AugerDownLimitPin,MainCoverClosePin, GPIO)



# esp32 initialized
useUart=False
if "use_Esp32_uart" in  machine_profile: 
    if machine_profile.getboolean("use_Esp32_uart"):
        useUart=True
esp32ctl=ESP32Controller(useUart,MCUresetPin) 

Ind_handler=Induction_Handler(GPIO, InductionPin)

def restart_USB_LAN_power():
    os.system("sudo sh -c 'echo 1-1 > /sys/bus/usb/drivers/usb/unbind'")
    print "off usb"
    time.sleep(2)

    os.system("sudo sh -c 'echo 1-1 > /sys/bus/usb/drivers/usb/bind'")
    print "on usb"
    time.sleep(2)

def AugerEngage():
    global cover_interrupt
    esp32ctl.motorSpeedControl(8)
    cover_interrupt=False
    time.sleep(1.25)
 #   motorSpeedControl(0)
    #time.sleep(1)
    GPIO.output(VtclmotorDownPin, 1)
    while not cs1.checkAugerDown():
        time.sleep(0.001)
        esp32ctl.currentReadingOnce()
        if not cs1.checkDoorClose():
            GPIO.output(VtclmotorDownPin, 0)
            esp32ctl.motorSpeedControl(0)
            return False
        else:
            GPIO.output(VtclmotorDownPin, 1)
        if cover_interrupt:
            esp32ctl.motorSpeedControl(8)
            cover_interrupt=False
            time.sleep(1.25)
    time.sleep(0.5) # hold the linear actuator down for extra time to maintain balance.
    esp32ctl.motorSpeedControl(0)
    GPIO.output(VtclmotorDownPin,0)
    time.sleep(0.3)
    return True


# def AugerInOut():
#     print("Auger in , Auger Out")
#     GPIO.output(VtclmotorUpPin,1) # plateform moving up
#     timers=time.time()
#     while (not cs1.checkAuger2nd() and not cs1.checkAugerUp()): # until hit 2nd high proximity
#         if int(time.time()-timers)%4 ==3 :
#             GPIO.output(VtclmotorUpPin,1)
#     GPIO.output(VtclmotorUpPin, 0)  # plateform moving up
#     #motorAugerInOut(60) ## perform turn 45 degree and return 45 degree
#     time.sleep(2)
#     GPIO.output(VtclmotorDownPin, 1) # plateform moving down
#     timers=time.time()
#     while not cs1.checkAugerDown(): # until hit down limit
#         if int(time.time()-timers)%4 ==3 :
#             GPIO.output(VtclmotorDownPin,1)
#     GPIO.output(VtclmotorDownPin, 0)  # plateform moving down

def AugerDisengage():
    # global angleoffsetX,angleoffsetY
    # angleoffsetX,angleoffsetY=offsetAngle()
    
    GPIO.output(VtclmotorUpPin,1)
    timers=time.time()
    while not cs1.checkAugerUp() :
        if int(time.time()-timers)%4 ==3 :
            GPIO.output(VtclmotorUpPin,1)
        time.sleep(0.001)

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
    global cover_interrupt
    print("motor process start")

    # print "Auger in auger out"
    #AugerInOut()

    torqueSensor=""

    #motorReverse(20)
    time.sleep(0.5)
    print "start blending ...."
    zeroRawReading=0


    print "    -pulse process, zeroing:", zeroRawReading
    motorspeed=0

    timestart=time.time()
    newtonMeter=0


    pretime = time.time()

    
    if UPCInCsv:
        print "----->",menuFLAVOR ," found flavor in list of set"
    else:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
        
    

    esp32ctl.motorSpeedControl(0)
    time.sleep(1)

    blend_sequence=json.loads(loaded_csv["BLEND_SEQ"])
    heat_sequence=json.loads(loaded_csv["HEAT_SEQ"])
    flavourCalib_sequence=json.loads(loaded_csv["FLAVOUR_CALIB_SEQ"])
    esp32ctl.motorAccNSpeedControl(0,0)
    # time.sleep(0.2)
    ttltime=0
    blendheatttltime=0
    for bp in blend_sequence:
        if ttltime<(bp[0]+bp[3]):
            ttltime=(bp[0]+bp[3])
    for hp in heat_sequence:
        if ttltime<(hp[0]+hp[1]):
            ttltime=(hp[0]+hp[1])
    blendheatttltime=ttltime
    for sp in flavourCalib_sequence:
        ttltime+=sp[2]
    
    starttime =time.time()
    cover_interrupt=False
    selected_heat_id=0
    selected_blend_id=0
    heat_stage=0
    blend_stage=0
    timeonce=0
    print "start blending + heating Sequence =", loaded_csv["BLEND_SEQ"], "+",loaded_csv["HEAT_SEQ"]
    while True:
        if len(blend_sequence)>selected_blend_id:
            if blend_sequence[selected_blend_id][0]<=(time.time()-starttime) and blend_stage==0:
                print "run motor at time :",(time.time()-starttime)
                esp32ctl.motorAccNSpeedControl(blend_sequence[selected_blend_id][1],blend_sequence[selected_blend_id][2])
                blend_stage = 1
            if (blend_sequence[selected_blend_id][0]+blend_sequence[selected_blend_id][3])<=(time.time()-starttime) :
                try:
                    if blend_sequence[selected_blend_id+1][0]<=(time.time()-starttime):
                        print "continue next cycle without stoping motor"
                    else:
                        print "stop motor at time wait next cycle:",(time.time()-starttime)
                        esp32ctl.motorSpeedControl(0)
                except:
                    if blendheatttltime>(time.time()-starttime):
                        print "stop motor at time exception:",(time.time()-starttime)
                        esp32ctl.motorSpeedControl(0)     
                    else:
                        print "continue motor at time exception for flavour calib:",(time.time()-starttime)     
                              
                selected_blend_id+=1
                blend_stage = 0
        if len(heat_sequence)>selected_heat_id:
            if heat_sequence[selected_heat_id][0]<=(time.time()-starttime) and heat_stage==0:
                print "start heating at time :",(time.time()-starttime)
                esp32ctl.InductionSafetyOn(int((heat_sequence[selected_heat_id][1])))
                Ind_handler.run_induction()
                heat_stage = 1
            if (heat_sequence[selected_heat_id][0]+heat_sequence[selected_heat_id][1])<=(time.time()-starttime) :
                print "stop heating at time :",(time.time()-starttime)
                Ind_handler.stop_induction()
                selected_heat_id+=1
                heat_stage = 0
        if len(blend_sequence)<=selected_blend_id and len(heat_sequence)<=selected_heat_id:
            break
        if cover_interrupt: # interupt happened and return, the sequence is reset.
            starttime =time.time()
            cover_interrupt=False
            selected_heat_id=0
            selected_blend_id=0
            heat_stage=0
            blend_stage=0
        if timeonce!=int(time.time()-starttime) :
            timetoshow=int(ttltime-int(time.time()-starttime))
            timeonce=int(time.time()-starttime)
            infotransfer={"INFOP":"Time left: "+str(timetoshow)+"s"}
            MA2UI_pipe_write(json.dumps(infotransfer))
        time.sleep(0.05)

        #print "blend ends ",time.time()-startBlendTime
    Ind_handler.stop_induction()

    calib_stage=0
    selected_calibrate_id=0
    timeAcc=0
    istarttime=time.time()
    timeonce=-1
    print "start Flavour Calibrating Sequence ",loaded_csv["FLAVOUR_CALIB_SEQ"]
    while  len(flavourCalib_sequence)>selected_calibrate_id: 
        if (flavourCalib_sequence[selected_calibrate_id][2]+timeAcc)>=(time.time()-istarttime) and calib_stage==0:
                print "run motor at time :",(time.time()-starttime)
                esp32ctl.motorAccNSpeedControl(flavourCalib_sequence[selected_calibrate_id][0],flavourCalib_sequence[selected_calibrate_id][1]) 
                calib_stage=1           
        if (flavourCalib_sequence[selected_calibrate_id][2]+timeAcc)<=(time.time()-istarttime):
                print "change motor state at time :",(time.time()-starttime)
                calib_stage=0    
                timeAcc+=flavourCalib_sequence[selected_calibrate_id][2]
                selected_calibrate_id+=1

        if len(flavourCalib_sequence)<=selected_calibrate_id :
            break
        if cover_interrupt: # interupt happened and return, the sequence is reset.
            cover_interrupt=False
            calib_stage=0
            selected_calibrate_id=0
            timeAcc=0
            istarttime=time.time()
        if timeonce!=int(time.time()-starttime) :
            timetoshow=int(ttltime-int(time.time()-starttime))
            timeonce=int(time.time()-starttime)
            infotransfer={"INFOP":"Time left: "+str(timetoshow)+"s"}
            MA2UI_pipe_write(json.dumps(infotransfer))
        time.sleep(0.05)
    print "sequence end at :",(time.time()-starttime)


    esp32ctl.motorSpeedControl(0)
    time.sleep(1)


def motorSpinDispense(extraDisp):
    print("dispence start")
    global cover_interrupt
    if UPCInCsv:
        print "----->",menuFLAVOR ," found flavor in list of set"
    else:
        print "-----> WARNING:  cannot find flavor in list (use default blend)"
    if extraDisp:
        dispence_sequence=[[700,1000,10]] #extra dispence sequence
    else:    
        dispence_sequence=json.loads(loaded_csv["DISPENSE_SEQ"])
    print "[dispence_sequence]",dispence_sequence
    esp32ctl.motorAccNSpeedControl(0,0)
    # time.sleep(0.5)
    # for param in dispence_sequence:
    #     esp32ctl.motorAccNSpeedControl(param[0],param[1])
    #     time.sleep(param[2])

    cover_interrupt=False
    ttltime=0
    for sp in dispence_sequence:
        ttltime+=sp[2]
    dispence_stage=0
    selected_dispence_id=0
    timeAcc=0
    starttime=time.time()
    timeonce=-1
    while  len(dispence_sequence)>selected_dispence_id: 
        if (dispence_sequence[selected_dispence_id][2]+timeAcc)>=(time.time()-starttime) and dispence_stage==0:
                print "run motor at time :",(time.time()-starttime)
                esp32ctl.motorAccNSpeedControl(dispence_sequence[selected_dispence_id][0],dispence_sequence[selected_dispence_id][1]) 
                dispence_stage=1           
        if (dispence_sequence[selected_dispence_id][2]+timeAcc)<=(time.time()-starttime):
                print "change motor state at time :",(time.time()-starttime)
                dispence_stage=0    
                timeAcc+=dispence_sequence[selected_dispence_id][2]
                selected_dispence_id+=1

        if len(dispence_sequence)<=selected_dispence_id :
            break
        if cover_interrupt: # interupt happened and return, the sequence is reset.
            cover_interrupt=False
            dispence_stage=0
            selected_dispence_id=0
            timeAcc=0
            starttime=time.time()
        if timeonce!=int(time.time()-starttime) :
            timetoshow=int(ttltime-int(time.time()-starttime))
            timeonce=int(time.time()-starttime)
            infotransfer={"INFOP":"Time left: "+str(timetoshow)+"s"}
            MA2UI_pipe_write(json.dumps(infotransfer))
        time.sleep(0.05)

    time.sleep(0.1)
    esp32ctl.motorSpeedControl(0)
    extratime=0
    motortemp=motor_temperature.averageTemperature(1)
    print "[MotorTemperature] "+str(motortemp)

    
 
def MA2UI_pipe_write(input):
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
    global state,timerLastTempCheck,capsuleTemperature
    selectscreen('insertScn')
   
    AugerDisengage()

    print"   -platform reach up"
    # os.system("xset s on")
    # os.system("xset s 30")
    timestart = time.time()

    # while True:
        
    #     if not cs1.checkDoorClose():
    #         # os.system("xset s reset")
    #         # os.system("xset s off")
    #         if timestart+3<time.time()<timestart+3+15:
    #             buzzerTone(1)
    #         if cs1.checkCapsuleIn():
    #             print "   -door open and capsule insert"
    #             state = 'doorcloseInsertScnFun'
                
    #         #if capsule and door close detected
    #             break
    #     else:
    #         timestart = time.time()
    #     time.sleep(0.10)
    countdown=0
    pulloutflag=False
    updatetimestart = time.time()
    printflagReboot=False
    while True:

    
        if git_start_headercode!=get_git_headercode() or git_start_headercode_param!=get_git_headercode_param():
            if not printflagReboot: 
                print "rebooting for update, waiting for 5 min to complete update"
                printflagReboot=True
            if updatetimestart+300<time.time(): #update 1 min later oni restart
                os.system("sudo reboot")
        else:
            updatetimestart = time.time()
        
        if not cs1.checkDoorClose():
            state = 'doorcloseInsertScnFun'
            break

        #     selectscreen('doorcloseInsertScn')
        #     pulloutflag=True
        #     countdown=0
        #     if timestart+3<time.time()<timestart+3+15:
        #         buzzerTone(1)                
        #     #if capsule and door close detected
        # else:
        #     timestart = time.time()
        #     countdown+=1
            
        #     if pulloutflag==True and countdown>5:
        #         state = 'identifyScnFun'
        #         pulloutflag=False
        #         break




        # if cs1.checkCapsuleIn() and cs1.checkDoorClose():
            
        #     countdown+=1
        #     if countdown>5:
        #         print "   -door close and capsule insert"
        #         state = 'identifyScnFun'
        #         break
        # else:
           
        #     countdown=0
        time.sleep(0.10)

    buzzerTone(0)
    

    


def doorcloseInsertScnFun():

    print("state: doorcloseInsertScnFun")
    global state
    selectscreen('doorcloseInsertScn')
    
    timestart = time.time()
    st_doorclose_no_scntouch=time.time()
    screentouchflag=False
    printflag1=True
    shm_ma2ui[0]=False
    while True:
        
        if cs1.checkDoorClose() and screentouchflag:
            print " screen touched and doorclose"
            #if capsule and door close detected
            state = 'identifyScnFun'
            break
        if cs1.checkDoorClose() and not screentouchflag:
            if printflag1==True:
                print "no screen touch and doorclose"
                printflag1=False
            shm_ma2ui[0]=True
            if (time.time()-st_doorclose_no_scntouch)>10.0:
                state = 'insertScnFun'
                shm_ma2ui[0]=False
                break
        else:
            printflag1=True
            shm_ma2ui[0]=False
            st_doorclose_no_scntouch=time.time()



        if not cs1.checkDoorClose() and timestart+3<time.time()<timestart+3+15:
            buzzerTone(1)

        UI_piperead = UI2MA_FIFOOpenRead.read()
        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            st = UI_piperead
            pairlist_UI =  jsonOrganizeLoad(st)
            if "TOUCH" in pairlist_UI  :
                screentouchflag=True
        time.sleep(0.1)
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
    menuSOFT=3
    targetSOFT=3
    menuFLAVOR=""
    menuUPC=""
    loaded_csv={}
    QR_piperead = QR2MA_FIFOOpenRead.read()
    Qrtrigerstate=False
    # load softness if any update
    config.read('/home/pi/swirlgo_machine.conf')  
    if "Softness" in  machine_profile:
         targetSOFT=machine_profile["Softness"]
    else :
        print "selected default softness",targetSOFT
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

                    UPCInCsv,loaded_csv=find_UPC_n_SOFT_from_csv(menuUPC, targetSOFT)
                    menuBRAND=loaded_csv['BRAND']
                    menuTYPE=loaded_csv['DESERT_TYPE']
                    menuSOFT=loaded_csv['SOFTNESS_LVL']
                    menuFLAVOR=loaded_csv['FLAVOUR']
                    print "get menuFLAVOR:",menuFLAVOR, ", Softness:",menuSOFT

                    MA2UI_pipe_write(json.dumps(loaded_csv))
                    GPIO.output(QRscannerTrigerpin, 1)

                    if UPCInCsv:
                        state = 'recognizedScnFun'
                        break
                    else:
                        print "[WARN] QR code Not in floavourparam list, ID:", menuUPC, " Soft:",menuSOFT 
                        continue

            #filter barcode
            if "BRAND" in pairlist:
                menuBRAND = pairlist["BRAND"]

            if "DESERT_TYPE" in pairlist:
                menuTYPE = pairlist["DESERT_TYPE"]

            if "SOFTNESS_LVL" in pairlist:
                menuSOFT = pairlist["SOFTNESS_LVL"]
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
            state = 'insertScnFun'
            # UPCInCsv,loaded_csv=find_UPC_n_SOFT_from_csv('DEFAULT', menuSOFT)
            # menuBRAND=loaded_csv['BRAND']
            # menuTYPE=loaded_csv['TYPE']
            # menuSOFT=loaded_csv['SOFT']
            # menuFLAVOR=loaded_csv['FLAVOUR']
            # MA2UI_pipe_write(json.dumps(loaded_csv))
            GPIO.output(QRscannerTrigerpin, 1)
            break

        if (time.time()-timepass)>1:
            print "trigering QR"
            timepass = time.time()
            GPIO.output(QRscannerTrigerpin, Qrtrigerstate)
            Qrtrigerstate = not Qrtrigerstate

        if not cs1.checkDoorClose():
            state = 'insertScnFun'
            break
        time.sleep(0.1)


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

    state = 'removeScnFun_checkdoor'

def errorScnFun3(): ## no selection and time out
    global state
    selectscreen('errorScn3')
    time.sleep(3)
    state = 'removeScnFun_checkdoor'

def errorScnFun4(): #Temp of capsule is too high
    global state
    selectscreen('errorScn4')
    time.sleep(3)
    state = 'insertScnFun'#'scanCapsuleTemperatureScnFun'


def recognizedScnFun():

    print("state: recognizedScnFun")
    global state
    selectscreen('recognizedScn')
    #lock the door
    timestart=time.time()
    while True:
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
            state = 'insertScnFun'
            break
        time.sleep(0.05)

        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break



def blendingScnFun():

    print("state: blendingScnFun")
    global state
    selectscreen('blendingScn')
    if not AugerEngage():
        esp32ctl.motorSpeedControl(0)
        state='insertScnFun'
        AugerDisengage()
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
        time.sleep(0.05)
        # if cs1.checkTemperature()>29:
        #     state = 'errorScnFun2'
        #     break

def dispensingScnFun():

    print("state: dispensingScnFun")
    global state
    selectscreen('dispensingScn')
    motorSpinDispense(False)
    
    # AugerDisengage()
    #motor spin for a time period to blend out icecream
    print "[Sales] [4] "+menuUPC+ \
        " [5] "+loaded_csv["UPC"]+" [6] "+"A"+ \
        " [7] "+loaded_csv["BRAND"]+" [8] "+loaded_csv['FLAVOUR']+ \
        " [9] "+"H"+loaded_csv["HEAT_SEQ"]+"+B"+loaded_csv["BLEND_SEQ"]+"+D"+loaded_csv["DISPENSE_SEQ"]+ \
        " [10] "+str(0)+" [11] "+machine_profile["MID"]+ \
        " [12] "+str(2.50)+" [13] "+str(0.12)+" [14] "+machine_profile["flavour_branch"]

    state = 'extraDispensingScnFun'
def extraDispensingScnFun():
    print("state: extraDispensingScnFun")
    global state
    selectscreen('extraDispensingScn')
    param=[700,1000,30] #[acc, finalvelocity, time]
    while True:
        UI_piperead = UI2MA_FIFOOpenRead.read()
        if len(UI_piperead) > 1:
            print "UI2MA:", UI_piperead
            pairlist_UI =  jsonOrganizeLoad(UI_piperead)
            if "EXTDISP" in pairlist_UI :
                if pairlist_UI["EXTDISP"]:
                    selectscreen('dispensingScn')
                    motorSpinDispense(True)
                    selectscreen('extraDispensingScn')
                else:
                    state = 'removeScnFun_checkdoor'
                    break
        time.sleep(0.05)
    AugerDisengage()

# def smileyScnFun():

#     print("state: smileyScnFun")
#     global state
#     selectscreen('smileyScn')
#     AugerDisengage()
#     capsulecheckremoveflag=False

#     timestart=time.time()
#     selectedrating=0
#     while True:
#         #buzzerTone(1)
#         UI_piperead = UI2MA_FIFOOpenRead.read()

#         if len(UI_piperead) > 1:
#             print "UI2MA:", UI_piperead
#             st = UI_piperead
#             pairlist_UI =  jsonOrganizeLoad(st)
#             if "RATE" in pairlist_UI :
#                 selectedrating=int(pairlist_UI["RATE"])
#                 time.sleep(1)
#                 break
#         if (time.time() - timestart) > 5 or  (time.time() - timestart) < 0 :
#             break
#         if not cs1.checkCapsuleIn():
#             capsulecheckremoveflag=True
#     # state = 'removeScnFun'
#     buzzerTone(0)
#     print "[Sales] [4] "+menuUPC+ \
#          " [5] "+loaded_csv["UPC"]+" [6] "+"A"+ \
#          " [7] "+loaded_csv["BRAND"]+" [8] "+loaded_csv['FLAVOUR']+ \
#          " [9] "+loaded_csv["BLEND_SEQ"]+"+"+loaded_csv["DISPENSE_SEQ"]+ \
#          " [10] "+str(selectedrating)+" [11] "+machine_profile["MID"]+ \
#          " [12] "+str(2.50)+" [13] "+str(0.12)+" [14] "+machine_profile["customer_brand"]
    
#     if capsulecheckremoveflag:
#         state = 'doorcloseRemoveScnFun'
#     else:
#         state = 'removeScnFun_checkcapsule'

# def removeScnFun():

#     print("state: removeScnFun")
#     global state
#     selectscreen('removeScn')
#     #time.sleep(5)
#     AugerDisengage()

#     timestart = time.time()
#     while cs1.checkCapsuleIn():
#         if timestart+3<time.time()<timestart+3+15:
#             buzzerTone(1)
#         time.sleep(0.1)
#     state='insertScnFun'#'scanCapsuleTemperatureScnFun'

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
        time.sleep(0.1)
    buzzerTone(0)
    # state='smileyScnFun'
    state='insertScnFun'

# def removeScnFun_checkcapsule():

#     print("state: removeScnFun_checkcapsule")
#     global state
#     selectscreen('removeScn')
#     #time.sleep(5)
#     AugerDisengage()

#     timestart = time.time()
#     while cs1.checkCapsuleIn():
#         if timestart+3<time.time()<timestart+3+15:
#             buzzerTone(1)
#         time.sleep(0.1)
#     buzzerTone(0)
#     state='doorcloseRemoveScnFun'



# def doorcloseRemoveScnFun():

#     print("state: doorcloseRemoveScnFun")
#     global state
#     selectscreen('doorcloseRemoveScn')
#     timestart = time.time()
#     while True:

#         if cs1.checkDoorClose()  :
#             print "   -doorclose"
#             #if capsule and door close detected
#             state = 'insertScnFun'#'scanCapsuleTemperatureScnFun'
#             break
#         if cs1.checkCapsuleIn():
#             print "    -New capsule insert"
#             state="insertScnFun"
#             break
        
#         if timestart+3<time.time()<timestart+3+15:
#             buzzerTone(1)
#         time.sleep(0.1)
#     buzzerTone(0)




def main_coveropen_cb(coverSafetyPin):
    global cover_interrupt
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
    esp32ctl.motorSpeedControl(0) #motorstop
    Ind_handler.stop_induction() #induction heating stop
    GPIO.output(buzzerpin, 0) #buzzer stop
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
        time.sleep(0.05)
    print "[QUIT PAUSE ]quit cover open callback loop"
    cover_interrupt=True
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
def exit_safety(sig, frame):
    print('Stoping every thing for safety')
    Ind_handler.stop_induction()
    GPIO.output(buzzerpin, 0)
    esp32ctl.motorSpeedControl(0)
    
    sys.exit(0)


dispatch = {

    #'scanCapsuleTemperatureScnFun': scanCapsuleTemperatureScnFun,
    'insertScnFun': insertScnFun,
    # 'doorcloseRemoveScnFun': doorcloseRemoveScnFun,
    'doorcloseInsertScnFun':doorcloseInsertScnFun,
 
    'removeScnFun_checkdoor':removeScnFun_checkdoor,
    # 'removeScnFun_checkcapsule':removeScnFun_checkcapsule,

    'identifyScnFun': identifyScnFun,

    'readyScnFun':readyScnFun,
    'blendingScnFun': blendingScnFun,
    'recognizedScnFun': recognizedScnFun,
    'dispensingScnFun': dispensingScnFun,
    'extraDispensingScnFun':extraDispensingScnFun,
    # 'removeScnFun':removeScnFun,

    # 'smileyScnFun':smileyScnFun,

    'errorScnFun1': errorScnFun1,
    'errorScnFun2': errorScnFun2,
    'errorScnFun3': errorScnFun3,
    'errorScnFun4': errorScnFun4, #for temp sensor



}

state="insertScnFun"
print("Configuring motor")
esp32ctl.motorSpeedControl(0)
# signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, exit_safety)
signal.signal(signal.SIGTERM, exit_safety)
signal.signal(signal.SIGSEGV, exit_safety)


print("Wait for 5 Second for UI to bootup ")
time.sleep(5)

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
        main_coveropen_cb(MainCoverClosePin)
        print "cover_safety enable"
        GPIO.add_event_detect(MainCoverClosePin, GPIO.RISING,callback=main_coveropen_cb, bouncetime=100)
        
Ind_handler.stop_induction()


try :
    while True:
        dispatch[state]()  ##state machine
        run_command("vcgencmd measure_temp", "[CPUtemperature] ")
        run_command("free -h", "[Memory] ")
            # for screen test +++++++++++
            # for i in testlistofscreen:
            #     selectscreen(i)
            #     time.sleep(5)
            # ++++++++++++++++++++++++++++
except Exception: 
    print(traceback.format_exc())
    print('Stoping every thing for safety')
    Ind_handler.stop_induction()
    GPIO.output(buzzerpin, 0)
    esp32ctl.motorSpeedControl(0)

