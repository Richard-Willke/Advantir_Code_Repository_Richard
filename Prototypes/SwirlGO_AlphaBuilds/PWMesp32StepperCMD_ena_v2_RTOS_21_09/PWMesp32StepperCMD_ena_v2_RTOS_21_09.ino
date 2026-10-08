/*
 * Author: Raymond Chan Chee Leong
 * Description : RTOS: Servo Motor PWM controller 
 *               RTOS: Curent sensor analog reader   
 *               RTOS: double verification for induction driver
 *               
 * version: 2
 * 
 */
#if CONFIG_FREERTOS_UNICORE
#define ARDUINO_RUNNING_CORE 0
#else
#define ARDUINO_RUNNING_CORE 1
#endif

#include "pin_Config.hpp"
#include "ServoPWM_Handler.hpp"

bool Serial_for_Servo_available=false;
bool Serial_for_Induc_available=false;
bool Serial_for_Currt_available=false;
String sn;
String snServo;
String snInduc;
String snCurrt;

double current_reading=0;

static const uint8_t buf_len = 20;
static int led_delay = 500;   // ms

void TaskSerial_Handler( void *pvParameters );
void TaskServo_Handler( void *pvParameters );
void TaskInductionSafety_Handler( void *pvParameters );
void TaskCurrentMeasuring_Handler( void *pvParameters );

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(IND_PIN, OUTPUT);
    xTaskCreatePinnedToCore(
    TaskSerial_Handler
    ,  "TaskSerial_Handler"   // A name just for humans
    ,  1024  // This stack size can be checked & adjusted by reading the Stack Highwater
    ,  NULL
    ,  1  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  NULL 
    ,  ARDUINO_RUNNING_CORE);

  xTaskCreatePinnedToCore(
    TaskServo_Handler
    ,  "TaskServo_Handler"   // A name just for humans
    ,  10240  // This stack size can be checked & adjusted by reading the Stack Highwater
    ,  NULL
    ,  2  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  NULL 
    ,  ARDUINO_RUNNING_CORE);

  xTaskCreatePinnedToCore(
    TaskInductionSafety_Handler
    ,  "TaskInductionSafety_Handler"   // A name just for humans
    ,  1024  // This stack size can be checked & adjusted by reading the Stack Highwater
    ,  NULL
    ,  3  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  NULL 
    ,  ARDUINO_RUNNING_CORE);
  xTaskCreatePinnedToCore(
    TaskCurrentMeasuring_Handler
    ,  "TaskCurrentMeasuring_Handler"   // A name just for humans
    ,  1024  // This stack size can be checked & adjusted by reading the Stack Highwater
    ,  NULL
    ,  4  // Priority, with 3 (configMAX_PRIORITIES - 1) being the highest, and 0 being the lowest.
    ,  NULL 
    ,  ARDUINO_RUNNING_CORE);
}

void loop() {}

void TaskSerial_Handler(void *pvParameters)  // This is a task.
{
  (void) pvParameters;
  for (;;){    
    if (Serial.available()>0) {
      //Serial.println("seralavailabke");
      sn = Serial.readStringUntil('\n');
      digitalWrite(LED_BUILTIN, HIGH);
      
      if (sn[0]!='e') {
        Serial.flush();
        digitalWrite(LED_BUILTIN, LOW);
        vTaskDelay(100); 
        continue; //check address
      }
      Serial.println(sn);
      switch (sn[1]){
        case 'm':
          snServo=sn.substring(2);
          Serial_for_Servo_available=true;
          break;
        case 'i':
          snInduc=sn.substring(2);
          Serial_for_Induc_available=true;
          break;
        case 'c':
          Serial.print("cr");
          Serial.println(current_reading);
          break;                    
      } 
      digitalWrite(LED_BUILTIN, LOW);
      vTaskDelay(100); 
    } 
  }
}

void TaskServo_Handler(void *pvParameters) 
{
  (void) pvParameters;
  //initialize
  ServoPwmHandler servoPwmHandler;

  for (;;) // A Task shall never return or exit.
  {
    if (Serial_for_Servo_available){
      //startfreq = servoPwmHandler.freqnow;
      servoPwmHandler.SerialInCallBack(snServo);
      Serial_for_Servo_available=false;
      }
    servoPwmHandler.looping_callback();
    //servoPwmHandler.looping_callback(startfreq);
    vTaskDelay(10); 
  }
}

void TaskInductionSafety_Handler(void *pvParameters)  
{
  (void) pvParameters;
  
//  TickType_t xLastWakeTime = xTaskGetTickCount();
//  TickType_t onFrequency = 100; //delay for mS
//  TickType_t offFrequency = 200; //delay for mS

  for (;;)
  {
      if (Serial_for_Induc_available){
        
                 
        int commaidx = snInduc.indexOf(',');
        int duration = abs(snInduc.substring(0, commaidx).toInt());
        int currentlimitraw = snInduc.substring(commaidx + 1).toInt();

        long int starttime=millis();
        digitalWrite(IND_PIN, HIGH);
          
        Serial_for_Induc_available=false;
        bool overCurrentFlag=false;
        while ((millis()-starttime)<duration*1000){
          if(current_reading>currentlimitraw){
            overCurrentFlag=true;
            break;
          }
          vTaskDelay(300); 
        }
        digitalWrite(IND_PIN, LOW);
        
        if (overCurrentFlag){
          Serial.print("[Error]induction Over Current:");
          Serial.println(current_reading);
        }
        vTaskDelay(100);
        
      }else{
        vTaskDelay(150); 
        digitalWrite(IND_PIN, LOW);
      }     
  } 
}

void TaskCurrentMeasuring_Handler(void *pvParameters)  
{
  (void) pvParameters;
  int rawInputArray[]={0,0,0,0,0,0,0,0,0,0,0} ;
  byte len= sizeof(rawInputArray) / sizeof(rawInputArray[0]);
  int sumRawInput=0; 
  int sensorValue=0;

   // to be edit
   for (;;)
  {
    sumRawInput=0;
    //FILO 
    for(byte i=len - 1; i>0; i--)
    {
       rawInputArray[i] = rawInputArray[i-1];
       sumRawInput+=rawInputArray[i];
    }
    rawInputArray[0]=analogRead(CUR_PIN);
    sumRawInput+=rawInputArray[0];
    //Averaging
    current_reading=sumRawInput/len;
    //y=mx+c calibration
//    current_reading=(double)sensorValue;
    vTaskDelay(100); 
  } 
}
