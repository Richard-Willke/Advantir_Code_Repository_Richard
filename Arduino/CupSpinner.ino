#define pwmPin 10 //esp32: 14 arduino: 10
#define dirPin 12 //esp32: 12 arduino: 12
#define enPin  11 //esp32: 13 arduino: 11
#define startButton 2 //esp32: 34
bool working = false;
int delayTime;
//int movingAverage[10]= {0,0,0,0,0,0,0,0,0,0};
//int average;

void setup() {
  pinMode(pwmPin,OUTPUT);
  pinMode(dirPin,OUTPUT);
  pinMode(enPin,OUTPUT);
  pinMode(startButton,INPUT);
  digitalWrite(pwmPin,LOW);
  digitalWrite(dirPin,LOW);
  digitalWrite(enPin,HIGH);
  //Serial.begin(9600);
}

void loop() {
  working = digitalRead(startButton);  
  switch (working){
    case true:
      digitalWrite(enPin,LOW);
      break;
    case false:
      digitalWrite(enPin,HIGH);
      break;
  }
  //delayTime = max(1,(5000.0/1023.0)*analogRead(A0));
  /*
  average = average + delayTime - movingAverage[0];
  for(int i = 0; i<9; i++){
    movingAverage[i] = movingAverage[i+1];
  }
  movingAverage[9] = delayTime;
  delayTime = average;
  */
  /*
  switch(delayTime<1){
    case true:
      delayTime = 1;
      break;
    case false:
      break;
  }
  */
  //Serial.println(delayTime);
  
  digitalWrite(pwmPin,HIGH); 
  delayMicroseconds(delayTime); 
  digitalWrite(pwmPin,LOW); 
  delayMicroseconds(delayTime);
}
