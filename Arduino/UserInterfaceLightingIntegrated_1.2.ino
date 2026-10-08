//Author: Richard Fabian Willke
//Place: Advantir Innovations, SwirlGO, Singapore
//Date: 30.05.2022

//includes for the LED strip
#include <FastLED.h>
#define LED_PIN             8                             //signal pin for the LED strip
#define NUM_LEDS            30                            //total number of LEDs that are being used in the strip
#define FADING_SPEED        100                           //delay in milliseconds between two frames 
#define FADING_LENGTH       10                            //number of LEDs that are involved in the effect. Increasing the number will however also increase the computing time and might make the programmslower
#define NUMBER_OF_COLOURS   3                             //set of colors that you want to have in your code. Remember to add the GRB values in the colors matrix below. The order of fades goes from top to bottom and back to top again
CRGB leds[NUM_LEDS];                                      //initialize the number of LEDs with the FastLED library

//button & LED pins and their varibles
#define led1       2
#define led2       3
#define led3       4
#define button1    5
#define button2    6
#define button3    7
bool val1 = false;
bool val2 = false;
bool val3 = false;
//limit switches to determine the state of the machine
//#define topLimitSwitch          19
//#define bottomLimitSwitch       20
//LEDs for the softness values  
#define regularLED              9
#define firmLED                 10
#define softLED                 11
#define smoothieLED             12
#define capsuleLighterLEDStrip  13
#define removeCapLED            1
int firmnessLevelCounter = 0;

int colors[NUMBER_OF_COLOURS][3] = {{0, 0, 0},
                                    {210, 210, 210},  
                                    //{255, 255, 255},      //matrix for the GRB values of the colors. Feel free to change the values or add new colors to the LED strip's repertoire.      
                                    {170, 255, 56}};      //consider changing the ammount of colours too, as soon as you add or delete any of the already existing colours 
int fadingEffect[FADING_LENGTH][3][NUMBER_OF_COLOURS];    //matrix that will be filled with the RBG information for each LED that is being addressed during the ffading animation
int sequenceMatrix[FADING_LENGTH][3];                     //storage matrix that will be used in the loop() function. It copies a part of the fadingEffect - Matrix

void setup(){
  calculateFadingMatrices();
  //_________________________________________________________________________________________________________________________
  //make the first few lights brighter than rest
  fadingEffect[0][0][0] = 255; fadingEffect[0][1][0] = 255; fadingEffect[0][2][0] = 255;
  fadingEffect[1][0][0] = 255; fadingEffect[1][1][0] = 255; fadingEffect[1][2][0] = 255;
  fadingEffect[2][0][0] = 255; fadingEffect[2][1][0] = 255; fadingEffect[2][2][0] = 255;
  //_________________________________________________________________________________________________________________________
  
  //all output pins for the buttons' LEDs
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  
  //all input pins for the buttons
  pinMode(button1, INPUT);
  pinMode(button2, INPUT);
  pinMode(button3, INPUT);

  analogWrite(led1, 255); 
  analogWrite(led2, 255); 
  analogWrite(led3, 0);
  
  //tell the compiler which chip and which color space is being used for the strip
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.show();

  //pinMode(topLimitSwitch, INPUT);
  //pinMode(bottomLimitSwitch, INPUT);
  pinMode(regularLED, OUTPUT);
  pinMode(firmLED, OUTPUT);
  pinMode(softLED, OUTPUT);
  pinMode(smoothieLED, OUTPUT);
  pinMode(capsuleLighterLEDStrip, OUTPUT);
  pinMode(removeCapLED, OUTPUT);
  digitalWrite(regularLED, HIGH);
  digitalWrite(firmLED, LOW);
  digitalWrite(softLED, LOW);
  digitalWrite(smoothieLED, LOW);
  digitalWrite(capsuleLighterLEDStrip, LOW);
  digitalWrite(removeCapLED, LOW);
}



//main function
void loop(){  
  //read the input values of the buttons and execute the machine-interface protocol according to the input
  val1 = digitalRead(button1);
  val2 = digitalRead(button2);
  processingFlow(val1, val2);
} 






void calculateFadingMatrices(){ 
  for(int sequenceNumber=0; sequenceNumber<NUMBER_OF_COLOURS; sequenceNumber++){    
    //Calculate the values for all fading matrices
    int startValue[3] = {0, 0, 0};                                                  
    int endValue[3]   = {0, 0, 0};
    for(int i=0; i<NUMBER_OF_COLOURS; i++){
     for(int n=0; n<3; n++){
        switch(i){
         case NUMBER_OF_COLOURS-1:
           startValue[n] = colors[NUMBER_OF_COLOURS-1][n];
           endValue[n] = colors[0][n];
           break;
         default: 
           startValue[n] = colors[i][n];
           endValue[n] = colors[i+1][n];
           break;
       }
      }
      for(int k=0; k<3; k++){
        for(int m=0; m<FADING_LENGTH; m++){
          fadingEffect[m][k][i] =  startValue[k] - ((startValue[k] - endValue[k])*m)/(FADING_LENGTH-1);
        }
      }
    }
  }
}

void TopToDownFade(int sequenceColor){
  for(int i = 0; i < (NUM_LEDS+FADING_LENGTH-1); i++){
    if (i <= FADING_LENGTH){
      int counter = 0;
      for(int m = i; m >= max(0,(i-FADING_LENGTH)); m--){
        leds[m] = CRGB(fadingEffect[min(counter, FADING_LENGTH-1)][0][sequenceColor], fadingEffect[min(counter, FADING_LENGTH-1)][1][sequenceColor], fadingEffect[min(counter, FADING_LENGTH-1)][2][sequenceColor]);
        counter++;
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    }  
    else if((i > FADING_LENGTH) && (i < NUM_LEDS)){
      for(int m = i; m > (i-FADING_LENGTH); m--){
        leds[m] = CRGB(fadingEffect[abs(m-i)][0][sequenceColor], fadingEffect[abs(m-i)][1][sequenceColor], fadingEffect[abs(m-i)][2][sequenceColor]);
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    }
    else if(i >= NUM_LEDS){
      for(int z = NUM_LEDS-1; z > (i-FADING_LENGTH); z--){
        leds[z] = CRGB(fadingEffect[i-z][0][sequenceColor], fadingEffect[i-z][1][sequenceColor], fadingEffect[i-z][2][sequenceColor]);
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    } 
    else{} 
  }
}

void BottomToTopFade(int sequenceColor){
  for(int i = (NUM_LEDS-1); i > (-FADING_LENGTH); i--){
    if (i >= (NUM_LEDS-FADING_LENGTH)){
      for(int m = i; m <= min((NUM_LEDS-1),(i+FADING_LENGTH-1)); m++){
        leds[m] = CRGB(fadingEffect[m-i][0][sequenceColor], fadingEffect[m-i][1][sequenceColor], fadingEffect[m-i][2][sequenceColor]);
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    }  
    else if((i >= 0) && (i < (NUM_LEDS-FADING_LENGTH))){
      for(int m = i; m < (i+FADING_LENGTH); m++){
        leds[m] = CRGB(fadingEffect[m-i][0][sequenceColor], fadingEffect[m-i][1][sequenceColor], fadingEffect[m-i][2][sequenceColor]);
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    }
    else if(i < 0){
      for(int m = 0; m < (i+FADING_LENGTH); m++){
        leds[m] = CRGB(fadingEffect[abs(i)+m][0][sequenceColor], fadingEffect[abs(i)+m][1][sequenceColor], fadingEffect[abs(i)+m][2][sequenceColor]);
      }
      FastLED.show(); 
      delay(FADING_SPEED);
    } 
    else{} 
  }
}

void adjustFirmnessLevels(){
  firmnessLevelCounter++;
  switch(firmnessLevelCounter % 4){ //adjust firmness settings accordingly
    case 0:
      digitalWrite(regularLED, HIGH);
      digitalWrite(firmLED, LOW);
      digitalWrite(softLED, LOW);
      digitalWrite(smoothieLED, LOW);
      break;
    case 1:
      digitalWrite(regularLED, LOW);
      digitalWrite(firmLED, HIGH);
      digitalWrite(softLED, LOW);
      digitalWrite(smoothieLED, LOW);
      break;
    case 2:
      digitalWrite(regularLED, LOW);
      digitalWrite(firmLED, LOW);
      digitalWrite(softLED, HIGH);
      digitalWrite(smoothieLED, LOW);
      break;
    case 3: 
      digitalWrite(regularLED, LOW);
      digitalWrite(firmLED, LOW);
      digitalWrite(softLED, LOW);
      digitalWrite(smoothieLED, HIGH);
      break;
  }
}

void processingFlow(bool value_1, bool value_2){
  if(value_1 == 1){ 
    //User is satisfied with the firmness level and wants to start the programm
    for(int i=255; i>0; i--){
      analogWrite(led2, i);
      delay(5);
    }
    
    BottomToTopFade(0);                                               //Capsule holder ascends 
    digitalWrite(capsuleLighterLEDStrip, HIGH);                       //Capsule holder reached final position
    delay(3000);                                                      //here will the code for the blending process go
    digitalWrite(removeCapLED, HIGH);                                 //Machine waits for user to remove cap. As soon as button 1 is being pressed again, the machine moves on with the dispense

    bool buttonOnePress = digitalRead(button1);
    while(buttonOnePress != 1){buttonOnePress = digitalRead(button1);}//!!!!!!!!!!!!!!!!!!!gotta implement the pausing in, too
    digitalWrite(removeCapLED, LOW);                                  
    TopToDownFade(1);
    for(int i=0; i<255; i++){
      analogWrite(led3, i);
      delay(5);
    }
    
    while(digitalRead(button3) == false){                             //dispensing is complete. Waiting for either additional dispense or end of sequence 
      //repeateadly dispensing until satisfied
      switch(digitalRead(button1)){
        case true:
          for(int i=255; i>0; i--){
            analogWrite(led3, i);
            delay(5);
          }
          delay(3000);
        default:
          analogWrite(led3, 255);
      }
    }

    digitalWrite(capsuleLighterLEDStrip, LOW);                      
    for(int i=255; i>0; i--){
      analogWrite(led1, i);
      delay(5);
    }
    
    //light up the lock button. Take input to lock or unlock auger

    TopToDownFade(2);                                               //dispensing complete. descend holder
    firmnessLevelCounter = -1;                                      //reset firmness level
    adjustFirmnessLevels();
  }
  
  else if(value_2 == 1){ 
    //as long as the sequence has not started, the user can switch between firmness levels
    adjustFirmnessLevels();
    delay(1500);    
  }
  
  else{
    //The system is in standby and wants orders
    analogWrite(led1, 255); 
    analogWrite(led2, 255); 
    analogWrite(led3, 0);
  }
}
