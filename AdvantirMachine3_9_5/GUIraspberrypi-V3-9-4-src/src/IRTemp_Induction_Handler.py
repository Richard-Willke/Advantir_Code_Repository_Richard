import io_param 
import numpy as np
import json
import time

class IRtemp_Induction_Handler():
    def __init__(self, GPIO, ser, engagepin,inductionpin):
        self.GPIO=GPIO
        self.ser=ser
        self.engagepin=engagepin
        self.inductionpin=inductionpin
        self.GPIO.setup(engagepin, GPIO.IN)
        self.GPIO.setup(inductionpin, GPIO.OUT)
    def getIRTemp(self,buffer):

        temperatureArray=np.ones(buffer)*-100.0
        countloop=0
        i=[0x01,0x03,0x00,0x00,0x00,0x01,0x84,0x0A]
        while True: #tempsensorLimitPin is engaged
        # temp = .....
            
            self.GPIO.output(io_param.IRTempTrigPin,1)#enable to write
            time.sleep(0.1)
            self.ser.write(i)
            self.ser.flush()
            self.GPIO.output(io_param.IRTempTrigPin,0)#enable to read
            if self.GPIO.input(self.engagepin):
                print "[Warning] capsule not insert well"
                return -100 
            #time.sleep(0.1)
            Arr=""
            while True:
                a=self.ser.read()
                Arr+=a
                #print(type(a))
                if len(a) ==0 or len(Arr)==7:
                    break

            if len(Arr)!=7:
                print "not data received"
            else:
                value = int(Arr[3:5].encode("hex"), 16)
                if value > 32768:
                    value = value- 65535
                temperatureArray[countloop%buffer] = value/10.0

            if countloop>buffer:
                max=np.amax(temperatureArray)
                min= np.amin(temperatureArray)
                if max-min>0.5 or np.mean(temperatureArray)==-100:
                    print "reading not stable", min, max
                else:
                    return np.mean(temperatureArray)
            if  countloop>buffer*100:
                break

            countloop+=1
        return -100

    def get_induction_heating_time(self,temp, loaded_csv ):
        if -20>temp:
            key="T:"+str(int(-20))
        elif temp>-10.0:
            key="T:"+str(int(-10))
        else:
            key="T:"+str(int(temp))
        timeduration=json.loads(loaded_csv[key])
        return timeduration
    def run_induction(self ):
        self.GPIO.output(self.inductionpin,1)
 

    def stop_induction(self):
        self.GPIO.output(self.inductionpin,0)
            


        





