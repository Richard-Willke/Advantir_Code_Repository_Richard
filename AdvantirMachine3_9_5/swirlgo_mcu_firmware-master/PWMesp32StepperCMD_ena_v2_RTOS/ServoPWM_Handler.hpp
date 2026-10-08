#include "pin_Config.hpp"
//#include "driver/ledc.h"
class ServoPwmHandler{
  public:
    ServoPwmHandler();
    ~ServoPwmHandler();
    void SerialInCallBack(String &sn);
    void looping_callback();
  private:
    int s ;
    float freqnow ;
    long int writtenfreq ;
    int ledChannel;
    int resolution; //Resolution 8, 10, 12, 15
    
    bool attachpin;
    
    float accel_freq ;
    int stay_freq;
    bool motor_exec_accel ;
    bool motor_exec_decel ;
    int duty_on ;
    float timestartaccel;
};
ServoPwmHandler::~ServoPwmHandler(){
  
}
ServoPwmHandler::ServoPwmHandler(){
    s = 0;
    freqnow = 0.0;
    writtenfreq = 0;
    ledChannel = 2;
    resolution = 2; //Resolution 8, 10, 12, 15
   
    
    attachpin = false;
    
    accel_freq = 0.0;
    stay_freq = 0;
    motor_exec_accel = false;
    motor_exec_decel = false;
    duty_on = 60;
    timestartaccel = micros();


    pinMode(DIR_PIN, OUTPUT); //DIR on ==cw, off == anticw
    pinMode(ENA_PIN, OUTPUT); //ENA on ==motor Off, off== motor on
    
    pinMode(PWM_PIN, OUTPUT); //PWM for motor
    digitalWrite(DIR_PIN, LOW);
    digitalWrite(ENA_PIN, LOW);
    ledcSetup(ledChannel, freqnow, resolution);
  
    int dutycycle = 2; // half for 2 bit -> 2^2
    ledcWrite(ledChannel, dutycycle);
    // tone(4,1000000);

}
void ServoPwmHandler::SerialInCallBack(String &sn){
     switch (sn[0]) {
      case 's':
        {
          //stop motor
          //Serial.println("motor stop");
          digitalWrite(ENA_PIN, LOW);
//          delay(300);
          vTaskDelay(300); 

          ledcDetachPin(PWM_PIN);
          attachpin = false;
          freqnow=0;
          stay_freq=0;
          

          ledcWriteTone(ledChannel, 0);
          //    analogWriteFrequency(PWM_PIN,0);
          //    analogWrite(PWM_PIN,125);
        }
        break;


      case 'r':
        {
          //Serial.println("reverse forward");
          sn.remove(0, 1);
          ledcDetachPin(PWM_PIN);
          attachpin = false;
          digitalWrite(DIR_PIN, HIGH);


          int Nostep = int(sn.toInt());
          for (int i = 0; i < Nostep; i++) {

            digitalWrite(PWM_PIN, HIGH);
//            delay(1);
            vTaskDelay(10); 
            digitalWrite(PWM_PIN, LOW);
//            delay(1);
            vTaskDelay(10); 

          }
          digitalWrite(DIR_PIN, HIGH);
          for (int i = 0; i < Nostep; i++) {
            digitalWrite(PWM_PIN, HIGH);
//            delay(1);
            vTaskDelay(10); 
            digitalWrite(PWM_PIN, LOW);
//            delay(1);
            vTaskDelay(10); 

          }
        }
        break;
      //reverse step

      case 'k':
        {
          //Serial.println("reverse");
          sn.remove(0, 1);

          pinMode(PWM_PIN, OUTPUT);
          digitalWrite(DIR_PIN, HIGH);

          int Nostep = int(sn.toInt());
          for (int i = 0; i < Nostep; i++) {

            digitalWrite(PWM_PIN, HIGH);
//            delay(1);
            vTaskDelay(10); 
            digitalWrite(PWM_PIN, LOW);
//            delay(1);
            vTaskDelay(10); 
          }
        }
        break;

      case 'a':
        {
          if (!attachpin) {
            ledcAttachPin(PWM_PIN, ledChannel);
            attachpin = true;
          }
          //Serial.println("auto acceleration");
          digitalWrite(ENA_PIN, HIGH);
          
          sn.remove(0, 1);
          int commaidx = sn.indexOf(',');
          accel_freq = abs(sn.substring(0, commaidx).toFloat());
          stay_freq = sn.substring(commaidx + 1).toFloat();
          if (stay_freq != int(freqnow)) {
            timestartaccel = micros();
          }

        }
        break;

        
      case 'f':
        {
        if (!attachpin) {
          ledcAttachPin(PWM_PIN, ledChannel);
          attachpin = true;
        }
        digitalWrite(ENA_PIN, HIGH);
//        digitalWrite(DIR_PIN, LOW);
        sn.remove(0, 1);
        stay_freq = int(sn.toInt());
        accel_freq=10000;
        timestartaccel = micros();

        }
        break;


    }
}
void waitUntilPulseChange(int pin, bool state, int duration) //duration in micro second, 
{
    int starttime=micros();
    bool statecheck=state;
    if (digitalRead(pin)==!statecheck){
      for(;;){
        if (digitalRead(pin)==statecheck or micros()-starttime>duration)break;
      }
    }
    for(;;){
        if (digitalRead(pin)==!statecheck or micros()-starttime>duration)break;
    }
}
void ServoPwmHandler::looping_callback(){
   if (int(freqnow) < stay_freq) {
    freqnow += accel_freq * float((micros() - timestartaccel) / 1000000.00);
    timestartaccel = micros();
    freqnow = (freqnow>stay_freq) ? stay_freq : freqnow;
    
  }

  else  if (int(freqnow) > stay_freq) {
    freqnow -= accel_freq * float((micros() - timestartaccel) / 1000000.00);
    timestartaccel = micros();
    freqnow = (freqnow<stay_freq) ? stay_freq : freqnow;
  }

  if (writtenfreq != int(freqnow)) 
//    Serial.println(freqnow);
  {
    writtenfreq = int(freqnow);
    if (writtenfreq>0) //if positive
      digitalWrite(DIR_PIN, LOW);
    else // if negaive
      digitalWrite(DIR_PIN, HIGH);
    

    waitUntilPulseChange(PWM_PIN,false,100000);
    ledcWriteTone(ledChannel, abs(writtenfreq));

  }
}
