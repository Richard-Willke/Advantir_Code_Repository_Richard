
#define DIR_PIN 32//3
#define ENA_PIN 25//5
#define PWM_PIN 33//4
 

int s = 0;
float freqnow = 0.0;
long int writtenfreq = 0;
const int ledChannel = 2;
const int resolution = 2; //Resolution 8, 10, 12, 15
String sn;

bool attachpin = false;

float accel_freq = 0.0;
int stay_freq = 0;
bool motor_exec_accel = false;
bool motor_exec_decel = false;
int duty_on = 60;
float timestartaccel = micros();

void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  pinMode(DIR_PIN, OUTPUT); //DIR on ==cw, off == anticw
  pinMode(ENA_PIN, OUTPUT); //ENA on ==motor Off, off== motor on
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PWM_PIN, OUTPUT); //PWM for motor
  digitalWrite(DIR_PIN, LOW);
  digitalWrite(ENA_PIN, HIGH);
  ledcSetup(ledChannel, freqnow, resolution);

  int dutycycle = 2; // half for 2 bit -> 2^2
  ledcWrite(ledChannel, dutycycle);
  // tone(4,1000000);
  //analogWrite(4,125);
}



void loop() {

  // put your main code here, to run repeatedly:
  if (Serial.available()) {
    digitalWrite(LED_BUILTIN, HIGH);
    sn = Serial.readStringUntil('\n');
    Serial.println(sn);
    Serial.flush();
    switch (sn[0]) {
      case 's':
        {
          //stop motor
          //Serial.println("motor stop");
          digitalWrite(ENA_PIN, HIGH);
          delay(300);

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
          digitalWrite(DIR_PIN, LOW);


          int Nostep = int(sn.toInt());
          for (int i = 0; i < Nostep; i++) {

            digitalWrite(PWM_PIN, HIGH);
            delay(1);
            digitalWrite(PWM_PIN, LOW);
            delay(1);

          }
          digitalWrite(DIR_PIN, HIGH);
          for (int i = 0; i < Nostep; i++) {
            digitalWrite(PWM_PIN, HIGH);
            delay(1);
            digitalWrite(PWM_PIN, LOW);
            delay(1);

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
            delay(1);
            digitalWrite(PWM_PIN, LOW);
            delay(1);
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
          digitalWrite(ENA_PIN, LOW);
          digitalWrite(DIR_PIN, LOW);
          sn.remove(0, 1);
          int commaidx = sn.indexOf(',');
          accel_freq = sn.substring(0, commaidx).toFloat();
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
        digitalWrite(ENA_PIN, LOW);
        digitalWrite(DIR_PIN, LOW);
        sn.remove(0, 1);
        stay_freq = int(sn.toInt());
        accel_freq=10000;
        timestartaccel = micros();

        }
        break;


    }
  }
  digitalWrite(LED_BUILTIN, LOW);

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


  if (writtenfreq != int(freqnow)) {
    writtenfreq = int(freqnow);
    ledcWriteTone(ledChannel, writtenfreq);
    delay(1);
    //Serial.println(freqnow);
  }



}
