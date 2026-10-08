//Defines pins and variables with their initial value for Arduino UNO
#define stepPin            11      //motor 1 is the linear motor
#define dirPin             10
#define enPin              9 
#define stepPin2           6       //originally pin 3       //motor 2 is the auger motor
#define dirPin2            5
#define enPin2             4
#define securityButton     8       //button on top
#define securityButton2    12      //button on bottom
#define startButtonL        3       //button to start the sequence
#define startButtonR        2       //button to start the sequence
#define automatedSwitch    1
#define recalSwitch        7     
bool buttonPressTop    =   true;   //with the current wiring: true = button not pressed
bool buttonPressBottom =   true;   //bottom button has same wiring as top button
bool startMachine      =   false;  //start button is false wenn not pressed
int  state             =   1;      //initial state is the standby state
bool startButtonRead   =   false;
int  counter           =   0;
bool inserted          =   false;
bool automated         =   false;
bool recal             =   false;
bool initial_cal       =   false;

void setup() {
  pinMode(automatedSwitch, INPUT);
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  pinMode(enPin,OUTPUT);
  pinMode(stepPin2,OUTPUT); 
  pinMode(dirPin2,OUTPUT);
  pinMode(enPin2,OUTPUT);
  pinMode(securityButton,INPUT);
  pinMode(securityButton2,INPUT);
  pinMode(startButtonL, INPUT);
  pinMode(startButtonR, INPUT);
  digitalWrite(dirPin,HIGH);
  digitalWrite(enPin,LOW);
  digitalWrite(enPin2,LOW);
  //Serial.begin(9600);
}

void loop() {
  
  //phase 1: move the motor up until switch is pressed 
  double i = 0;
  while(state == 1){
    buttonPressTop = digitalRead(securityButton);
    startButtonRead = (digitalRead(startButtonL) && digitalRead(startButtonR));
    if(buttonPressTop == true){
      digitalWrite(enPin,HIGH);
      digitalWrite(enPin2,HIGH);
      digitalWrite(dirPin,LOW);
      digitalWrite(dirPin2,HIGH);
    }
    else{
      digitalWrite(enPin,LOW);
      digitalWrite(enPin2,LOW);
    }
    
    if (counter < 1000){
      digitalWrite(stepPin2,HIGH);
      for(int j = 0; j<3; j++){   
        digitalWrite(stepPin,HIGH); 
        delayMicroseconds(3); 
        digitalWrite(stepPin,LOW); 
        delayMicroseconds(7);
      }
      
      digitalWrite(stepPin2,LOW);
      for(int j = 0; j<4; j++){   
        digitalWrite(stepPin,HIGH); 
        delayMicroseconds(3); 
        digitalWrite(stepPin,LOW); 
        delayMicroseconds(7);
      }
      counter++;
    }
    
    else{
      digitalWrite(stepPin2,HIGH);
        for(int j = 0; j<3; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
      digitalWrite(stepPin2,LOW);
        for(int j = 0; j<4; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
    }
          
    buttonPressTop = digitalRead(securityButton);
    startButtonRead = (digitalRead(startButtonL) && digitalRead(startButtonR));
    automated = digitalRead(automatedSwitch);
    initial_cal = buttonPressTop;
    if(initial_cal == false){
      switch(startButtonRead || automated){
        case true: 
          counter = 0;
          digitalWrite(enPin,LOW);
          digitalWrite(enPin2,LOW);
          //delay(100);
          if(inserted == false){state = 2;}
          else{state = 3;}
          break;
        case false:
          break;
      }
    }
    else{}

    //buttonPressTop = digitalRead(securityButton);
    switch(buttonPressTop){
      case true:
        //state = 1; 
        break;
      case false:
        inserted = false;        
        if (startButtonRead == true){
          counter = 0;
          digitalWrite(enPin,LOW);
          digitalWrite(enPin2,LOW);
          delay(1);
          state = 2;
        }
        else{
          counter = 0;
          digitalWrite(enPin,LOW);
          digitalWrite(enPin2,LOW);
          delay(1);
          state = 4;
        }
        break;
    }
  }

  
  //phase 2: going down with first motor

  while(state == 2){
    digitalWrite(enPin,HIGH);
    digitalWrite(enPin2,HIGH);
    digitalWrite(dirPin,HIGH);
    digitalWrite(dirPin2,LOW);
    inserted = false; 
    i = 0;
    buttonPressBottom = digitalRead(securityButton2);
    while((i < 1000) || (buttonPressBottom == true)){ //usually AND. For testig this time logical OR+
    //while((buttonPressBottom == true)){
      buttonPressBottom = digitalRead(securityButton2);
      
      if(i<1000){
        digitalWrite(stepPin2,HIGH);
        for(int j = 0; j<3; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(2); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(5);
        }
        
        digitalWrite(stepPin2,LOW);
        for(int j = 0; j<4; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(2); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(5);
        } 
        i++;
      }
      
      else{
        digitalWrite(stepPin2,HIGH);
        for(int j = 0; j<3; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
      
        digitalWrite(stepPin2,LOW);
        for(int j = 0; j<4; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
      }
      
      startButtonRead = (digitalRead(startButtonL) && digitalRead(startButtonR));
      automated = digitalRead(automatedSwitch);
      switch(startButtonRead || automated){
        case false:
          state = 1;
          buttonPressBottom = false;
          i = 1000;
          break;
        case true:
          //state = 2;
          break;
      }
    }
    digitalWrite(enPin,LOW);
    digitalWrite(enPin2,LOW);
    delay(1);
    buttonPressBottom = digitalRead(securityButton2);
    if(buttonPressBottom == false){
      inserted = true;
    }
    state = 3; 
  }
  
  //phase 3: letting go of auger. Moving up again, until switch pressed again
  while(state == 3){
    i = 1000;
    digitalWrite(enPin,HIGH);
    digitalWrite(enPin2,HIGH);
    digitalWrite(dirPin,LOW);
    digitalWrite(dirPin2,HIGH);
    buttonPressTop = digitalRead(securityButton);
    while((i > 0) || (buttonPressTop == true)){ //usually AND. For thesting reasons changed to logical OR
    //while((buttonPressTop == true)){
      buttonPressTop = digitalRead(securityButton);
      if (i>0){
        //digitalWrite(stepPin2,HIGH);
        for(int j = 0; j<3; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(3); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(7);
        }
        
        //digitalWrite(stepPin2,LOW);
        for(int j = 0; j<4; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(3); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(7);
        }
        
        i--;
      }
      else{
        //digitalWrite(stepPin2,HIGH);
        for(int j = 0; j<3; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
        //digitalWrite(stepPin2,LOW);
        for(int j = 0; j<4; j++){   
          digitalWrite(stepPin,HIGH); 
          delayMicroseconds(1); 
          digitalWrite(stepPin,LOW); 
          delayMicroseconds(1);
        }
      }
      startButtonRead = (digitalRead(startButtonL) && digitalRead(startButtonR));
      automated = digitalRead(automatedSwitch);
      switch(startButtonRead || automated){
        case false:
          state = 1;
          buttonPressTop = false;
          i = 0;
          break;
        case true:
          //state = 3;
          break;
      }
    }
    digitalWrite(enPin,LOW);
    digitalWrite(enPin2,LOW);
    delay(1);
    state = 4;
  }

  //phase 4: waiting for further input. this is the standby state. Exit it by pressing the start button
  while(state == 4){
    digitalWrite(enPin,LOW);
    digitalWrite(enPin2,LOW);
    startMachine = (digitalRead(startButtonL) && digitalRead(startButtonR));
    buttonPressTop = digitalRead(securityButton);

    switch(startMachine){
      case false:
        if(buttonPressTop == true){
          state = 1;
        }
        else{
          //state = 4; 
        }
        break;
      case true:
        state = 1;
        break;
    }
    delay(1);
  }
}
