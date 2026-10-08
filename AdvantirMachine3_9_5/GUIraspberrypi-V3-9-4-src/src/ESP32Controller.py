import time 
import RPi.GPIO as GPIO
import serial

class ESP32Controller:
    def __init__(self, useUart, MCUresetPin):


        if (useUart):
                self.motordevlist = ["ttyS0"]
        else:
            self.motordevlist = ["motordrive",
                "ttyACM0", 
                "ttyACM1", 
                "ttyUSB0",
                "ttyUSB1"]
        self.motordevroll=0
        self.MCUresetPin=MCUresetPin
        self.current_m=0.001
        self.current_c=1.0
        self.currentlimit=40.0 
        self.SerialConnecting()


    def SerialConnecting(self):
        # global ser,motordevroll
        print "finding ESP32"
        while True:
            connectlink='/dev/'+self.motordevlist[self.motordevroll] 
            try:
                self.ser = serial.Serial(connectlink,baudrate=9600,timeout=3)
                break
            except:
                self.motordevroll+=1
                self.motordevroll=self.motordevroll%len(self.motordevlist)
                if self.motordevroll==0:
                    self.resetMCU()

    def resetMCU(self):
        GPIO.output(self.MCUresetPin,0)
        time.sleep(0.5)
        GPIO.output(self.MCUresetPin,1)
        time.sleep(2)   

    def write2serial(self,towrite_tmp):
        # global ser
        writeFail=0 # input != output count
        writeOvertime=0
        while True:
            try:
                self.ser.flushInput()
                self.ser.flushOutput()
                #ser.write((towrite).encode('ascii'))
                startreadtime=time.time()
                towrite='e'+towrite_tmp
                self.ser.write((towrite).encode('ascii'))
                sn=self.ser.readline() 

                endreadtime=time.time()
                print "[ESP32 confirmation feedback]", sn.encode("unicode_escape").decode("utf-8"), "[input]", towrite.encode("unicode_escape").decode("utf-8"), " [time taken]","%.4f"%(endreadtime-startreadtime) 
                if  towrite[:-1] in sn:
                    break
                else:
                    writeFail+=1
                    if (endreadtime-startreadtime>2.5):
                        print "[ESP32 error]reading over time"
                        writeOvertime+=1
                        if (writeOvertime>2):
                            raise Exception("[ESP32 error]reading over time")
                    if (writeFail>=20):
                        writeFail=0
                        raise Exception('[ESP32 error] input != output from MCU')
            except:
                self.resetMCU()
                self.SerialConnecting()
                time.sleep(1)

    def motorSpeedControl(self, rpm):
        #rpm to frequency
        if (rpm==0):
            self.write2serial('ms\n')
        else:
            val= (rpm*1600*3)/60
            towrite = "mf"+str(val) + "\n"
            self.write2serial(towrite)


    def motorAccNSpeedControl(self, rpmps,rpm ):
        #rpm to frequency
        reachspeed= (rpm*1600*3)/60
        acc= (rpmps*1600*3*2)/60
        towrite = "ma"+str(acc) +","+str(reachspeed) +"\n"
        print (towrite)
        self.write2serial(towrite)

    def motorAugerInOut(self,deg):
        val=deg*3*1600/(360)
        towrite = "mr"+str(val) + "\n"
        self.write2serial(towrite)

    def motorStop(self):
        towrite = "mstop" + "\n"
        self.write2serial(towrite)

    def motorReverse(self,deg):
        val=deg*3*1600/(360)
        towrite = "mk"+str(val) + "\n"
        self.write2serial(towrite)

    def IOWrite(self, EIOpin,bit): # pin to switch, on(1) or off(0)
        towrite= "do"+str(EIOpin)+","+str(bit)+ "\n"
        self.write2serial(towrite)

    def IORead(self, EIOpin): # pin to switch, on(1) or off(0)
        towrite= "di"+str(EIOpin)+"\n"
        self.write2serial(towrite)
        sn=self.ser.readline() 
        endreadtime=time.time()
        if (sn[:2]=="\x17di"):
            print "got input reading:",sn[2:]
            raw=int(sn[2:])
            return bool(raw)
        else: 
            if (endreadtime-startreadtime>2.5):
                print " input reading overtime"
            else:
                print "wrong reply:", sn

    def InductionSafetyOn(self,duration): # ms
        currentlimitraw=(self.currentlimit-self.current_c)/self.current_m
        towrite= "i"+str(duration)+","+str(int(currentlimitraw))+"\n"
        self.write2serial(towrite)

    def currentReadingOnce(self):
        towrite= "cr\n"
        self.write2serial(towrite)
        startreadtime=time.time()
        sn=self.ser.readline() 
        endreadtime=time.time()
        if (sn[:2]=="cr"):
            print "got current raw reading:",sn[2:-2]
            raw=float(sn[2:-2])
            return self.current_m*raw+self.current_c
        else: 
            if (endreadtime-startreadtime>2.5):
                print " current reading overtime"
            else:
                print "wrong reply:", sn
        #read current 
