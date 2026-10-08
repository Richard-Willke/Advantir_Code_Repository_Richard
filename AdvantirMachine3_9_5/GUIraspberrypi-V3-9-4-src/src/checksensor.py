# from ds18b20 import DS18B20 # github rgbkrk/ds18b20
import time

# output event changes PRINT OUT:
#    [InputBit] <sensor id> <status>
# sensor id:
#    [0] DoorClosepin
#    [1] CapsuleInPin
#    [2] AugerUpLimitPin
#    [3] Auger2ndLimitPin
#    [4] AugerDownLimitPin
#    [5] CapPin

class sensing:

    def __init__(self, DoorClosepin,CapsuleInPin,AugerUpLimitPin,Auger2ndLimitPin,AugerDownLimitPin,IRcapdetectPin, GPIO):
        self.___DoorClosepin = DoorClosepin
        self.___CapsuleInPin = CapsuleInPin
        self.___AugerUpLimitPin = AugerUpLimitPin
        self.___Auger2ndLimitPin = Auger2ndLimitPin
        self.___AugerDownLimitPin = AugerDownLimitPin
        self.___IRcapdetectPin = IRcapdetectPin

        self.GPIO=GPIO
        self.GPIO.setup(CapsuleInPin, GPIO.IN)
        self.GPIO.setup(IRcapdetectPin, GPIO.IN)
        self.GPIO.setup(DoorClosepin, GPIO.IN)
        self.GPIO.setup(AugerUpLimitPin, GPIO.IN)
        self.GPIO.setup(AugerDownLimitPin, GPIO.IN)
        self.GPIO.setup(Auger2ndLimitPin, GPIO.IN)


        self.iostate=[-1]*6

        # self.sensorTemperature = DS18B20()


    def checkAllSensorEvent(self):
        k=[0]*6
        for i in range(6):
            k[0] = k[0] + self.GPIO.input(self.___DoorClosepin)
            k[1] = k[1] + self.GPIO.input(self.___CapsuleInPin)
            k[2] = k[2] + self.GPIO.input(self.___AugerUpLimitPin)
            k[3] = k[3] + self.GPIO.input(self.___Auger2ndLimitPin)
            k[4] = k[4] + self.GPIO.input(self.___AugerDownLimitPin)
            k[5] = k[5] + self.GPIO.input(self.___IRcapdetectPin)
        for i in len(k):
            if self.iostate[i]!=(k[i]<3):
                self.iostate[i] = k[i] < 3
                print("[InputBit] ",i," ", int(k[i] < 3))


    def checkDoorClose(self):

        k=0
   
        for i in range(10):
            k=k+self.GPIO.input(self.___DoorClosepin)

        return k<5

    def checkCapsuleIn(self):
        global GPIO
        k=0
 
        for i in range(10):
            k=k+self.GPIO.input(self.___CapsuleInPin)

        return k<5

    def checkCap(self):
        global GPIO
        k=0
     
        for i in range(10):
            k=k+self.GPIO.input(self.___IRcapdetectPin)

        return k<5

    def checkAugerUp(self):
        k=0
        for i in range(10):
            k=k+self.GPIO.input(self.___AugerUpLimitPin)

        return k<5

    def checkCapInTemp(self):
        k=0
    
        for i in range(10):
            k=k+self.GPIO.input(self.___Auger2ndLimitPin)

        return k<5

    def checkAugerDown(self):
        k=0
     
        for i in range(10):
            k=k+self.GPIO.input(self.___AugerDownLimitPin)


        return k<5


    def checkCapsuleSpinForce(self):
        return 1


    # def checkTemperature(self):
    #     temperature_in_celcius=self.sensorTemperature.get_temperature()
    #     return temperature_in_celcius