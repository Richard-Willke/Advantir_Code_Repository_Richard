from ds18b20 import DS18B20 # github rgbkrk/ds18b20

class ds18b20_temperature_setup:
    def __init__(self):
        self.temp_sensor_flag=False # if Flag is False mean sensor is fault, True is good to go.
        sensors = DS18B20.get_all_sensors()
        print "number of temperature detected ", len(sensors)
        if len(sensors)==0:
            return
        try :
            self.motor_temp_sensor = DS18B20()
            self.temp_sensor_flag=True
        except:
            self.temp_sensor_flag=False

    def motorMaxTemperature(self,maxtemp):
       
        current_motortemp=0

        if self.temp_sensor_flag==False:
            sensors = DS18B20.get_all_sensors()
            if len(sensors)==0:
                return 0
            try :
                self.motor_temp_sensor = DS18B20()
                self.temp_sensor_flag=True
            except:
                self.temp_sensor_flag=False

        try:
            if self.temp_sensor_flag:
                    current_motortemp = self.motor_temp_sensor.get_temperature()
            if maxtemp<current_motortemp:
                    maxtemp=current_motortemp    
        except:
            try :
                self.motor_temp_sensor = DS18B20()
                self.temp_sensor_flag=True
            except:
                self.temp_sensor_flag=False

        return maxtemp    

    def averageTemperature(self,num):
      
       # num=20
        current_motortemp=0

        if self.temp_sensor_flag==False:
            sensors = DS18B20.get_all_sensors()
            if len(sensors)==0:
                return 0
            try :
                self.motor_temp_sensor = DS18B20()
                self.temp_sensor_flag=True
            except:
                self.temp_sensor_flag=False

        try:
            if self.temp_sensor_flag:
                for i in range(num):
                    current_motortemp += self.motor_temp_sensor.get_temperature()
        except:
            try :
                self.motor_temp_sensor = DS18B20()
                self.temp_sensor_flag=True
            except:
                self.temp_sensor_flag=False

        return current_motortemp/num    
            