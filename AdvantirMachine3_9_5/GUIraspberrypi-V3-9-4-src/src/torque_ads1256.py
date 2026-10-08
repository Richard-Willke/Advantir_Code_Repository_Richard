import ads1256

class torque_ads1256_setup:
    def __init__(self,calibration):
        ads1256.start("64", "30000")
        self.arrayReading=[]
        self.calibration=calibration
        self.zeroRawReading
        self.accum_record=True

    def zeroing(self,samples):
        zeroRawReading=0
        zerocount=0
        prevalue1=0
       
        while zerocount<samples:
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
        self.zeroRawReading=zeroRawReading/samples
        return self.zeroRawReading

    def try_zeroing(self, samples):
        for i in range(3): # try 3 times if error
            try:
                return zeroing(samples)
            except:
                ads1256.start("64", "30000")
        return -999

    def raw_accumulating_mean(self) :

        rawindependent = ads1256.read_channel(0)
        if rawindependent>3000 or rawindependent==0 or rawindependent<-700: continue
        if abs(rawindependent-self.prevalue1)>300:
            self.prevalue1=rawindependent
            self.accum_record=False

        if self.accum_record==False and self.prevalue1!=rawindependent and  abs(rawindependent-prevalue1)<300:
            self.accum_record = True

        if  self.accum_record:
            self.prevalue1=rawindependent
            self.arrayReading.append(rawindependent)
            if len(self.arrayReading) > 100: 
                del self.arrayReading[0]
            averageRawReading = float(sum(self.arrayReading)) / len(self.arrayReading)
            return averageRawReading-self.zeroRawReading
    def init_accumulator(self):
        self.arrayReading=[]
        self.accum_record=True
        self.prevalue1 = self.zeroRawReading

    def convert_raw2newtonmeter(self,rawReading):
        newtonMeter = 2 * calibration * (rawReading )