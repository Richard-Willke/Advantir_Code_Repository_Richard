import io_param 
import numpy as np
import json
import time

class Induction_Handler():
    def __init__(self, GPIO, inductionpin):
        self.GPIO=GPIO
        self.inductionpin=inductionpin
        self.GPIO.setup(inductionpin, GPIO.OUT)
 
    def run_induction(self ):
        print "INDUCTION ON"
        self.GPIO.output(self.inductionpin,1)
 

    def stop_induction(self):
        print "INDUCTION OFF"
        self.GPIO.output(self.inductionpin,0)
            


        





