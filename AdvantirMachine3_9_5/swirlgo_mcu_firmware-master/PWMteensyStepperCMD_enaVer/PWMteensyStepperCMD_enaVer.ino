

int s = 0;
float freqnow = 0.0;
int writtenfreq=0;
String sn;
float accel_freq = 0;
float stay_freq = 0;
bool motor_exec_accel = false;
bool motor_exec_decel = false;
int duty_on=60;
float timestartaccel = micros();s
void setup() {
  // put your setup code here, to run once:

  Serial.begin(9600);
  pinMode(3, OUTPUT); //DIR on ==cw, off == anticw
  pinMode(5, OUTPUT); //ENA on ==motor Off, off== motor on
  // tone(4,1000000);
  //analogWrite(4,125);
  digitalWrite(3, HIGH);
  digitalWrite(5, HIGH);

}
int dutycycle(float freqnow){
  duty_on=0.000006*255.00*freqnow;
  return 85;
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available()) {
    sn = Serial.readStringUntil('\n');
    if (sn == "s" or sn == "stop" ) {
      //stop motor
      Serial.println("motor stop");
      digitalWrite(5, HIGH);
      delay(300);
      analogWriteFrequency_RC(4, 0);
      analogWrite(4, duty_on);
      motor_exec_accel = false;
      motor_exec_decel = false;
      freqnow=0;
      //delay(100);
      //digitalWrite(5,LOW);


    }
    else if (sn[0] == 'r')
    {
      digitalWrite(5, LOW);
      Serial.println("reverse");
      sn.remove(0, 1);
      pinMode(4, OUTPUT);
      digitalWrite(3, HIGH);

      int Nostep = int(sn.toInt());
      for (int i = 0; i < Nostep; i++) {

        digitalWrite(4, HIGH);
        delay(1);
        digitalWrite(4, LOW);
        delay(1);

      }
      digitalWrite(3, LOW);
      for (int i = 0; i < Nostep; i++) {
        digitalWrite(4, HIGH);
        delay(1);
        digitalWrite(4, LOW);
        delay(1);

      }
      //reverse step
    }
    else if (sn[0] == 'k') {
      digitalWrite(5, LOW);
      Serial.println("reverse");
      sn.remove(0, 1);
      pinMode(4, OUTPUT);
      digitalWrite(3, LOW);

      int Nostep = int(sn.toInt());
      for (int i = 0; i < Nostep; i++) {

        digitalWrite(4, HIGH);
        delay(1);
        digitalWrite(4, LOW);
        delay(1);
      }
    }

    else if (sn[0] == 'a') {
      Serial.println("auto acceleration");
      digitalWrite(5, LOW);
      digitalWrite(3, HIGH);
      sn.remove(0, 1);
      int commaidx = sn.indexOf(',');
      accel_freq = sn.substring(0, commaidx).toFloat();
      stay_freq = sn.substring(commaidx + 1).toFloat();
      if (stay_freq > freqnow) {
        motor_exec_accel = true;
        motor_exec_decel = false;
        timestartaccel = micros();
        analogWrite(4, dutycycle(freqnow));
      }
      if (stay_freq < freqnow) {
        motor_exec_decel = true;
        motor_exec_accel = false;
        timestartaccel = micros();
        analogWrite(4, dutycycle(freqnow));
      }
    }
    else if (int(sn.toInt()) >0)
    {
      digitalWrite(5, LOW);
      digitalWrite(3, HIGH);
      s = int(sn.toInt());
      
      analogWriteFrequency_RC(4, s);
      analogWrite(4, dutycycle(freqnow));
      Serial.println(s);
    }
  }


  if (motor_exec_accel) {
    if (freqnow < stay_freq) {
      freqnow += accel_freq * ((micros() - timestartaccel) / 1000000.0);
      timestartaccel = micros();
      if (writtenfreq!=int(freqnow)){
        writtenfreq=int(freqnow);
        uint8_t statuscheck=analogWriteFrequency_RC(4, int(freqnow));
        analogWrite(4, dutycycle(freqnow));
        Serial.println(freqnow);
      }
      //delay(100);
    }
    else {
      freqnow = stay_freq;
      if (writtenfreq!=int(freqnow)){
        writtenfreq=int(freqnow);
        analogWriteFrequency_RC(4, freqnow);
        analogWrite(4, dutycycle(freqnow));
      }
      motor_exec_accel = false;
      //delay(100);
    }
  }
  if (motor_exec_decel) {
    if (freqnow > stay_freq) {
      freqnow -= accel_freq * ((micros() - timestartaccel) / 1000000.0);
      timestartaccel = micros();
      if (writtenfreq!=int(freqnow)){
        writtenfreq=int(freqnow);
        analogWriteFrequency_RC(4, int(freqnow));
        analogWrite(4, dutycycle(freqnow));
      }
    }
    else {
      freqnow = stay_freq;

      if (writtenfreq!=int(freqnow)){
        writtenfreq=int(freqnow);
        analogWriteFrequency_RC(4, int(freqnow));
        analogWrite(4, dutycycle(freqnow));
        Serial.println(freqnow);
      }
      motor_exec_decel = false;
    }
  }
}


//  delay(100);
//  int sensorvalue=analogRead(A9);
//  int s=map(sensorvalue,0,1024,0,50000);
//
//  analogWriteFrequency(4,s);
//  analogWrite(4,125);
//  s+=1000;


/*
note for new laptop or fresh install teensy arduino compiler.
need to add function below to arduino-1.8.9/hardware/teensy/avr/cores/teensy3/pins_teensy.c , and add declare function to header core_pin.h
######## funtion #######
void analogWriteFrequency_RC(uint8_t pin, float frequency)
{
  uint32_t prescale, mod, ftmClock, ftmClockSource;
  float minfreq;

  //serial_print("analogWriteFrequency: pin = ");
  //serial_phex(pin);
  //serial_print(", freq = ");
  //serial_phex32((uint32_t)frequency);
  //serial_print("\n");

#ifdef TPM1_CH0_PIN
  if (pin == TPM1_CH0_PIN || pin == TPM1_CH1_PIN) {
    ftmClockSource = 1;
    ftmClock = 16000000;
  } else
#endif
#if defined(__MKL26Z64__)
  // Teensy LC does not support slow clock source (ftmClockSource = 2)
  ftmClockSource = 1;   // Use default F_TIMER clock source
  ftmClock = F_TIMER; // Set variable for the actual timer clock frequency
#else
  if (frequency < (float)(F_TIMER >> 7) / 65536.0f) {
    // frequency is too low for working with F_TIMER:
    ftmClockSource = 2;   // Use alternative 31250Hz clock source
    ftmClock = 31250;     // Set variable for the actual timer clock frequency
  } else {
    ftmClockSource = 1;   // Use default F_TIMER clock source
    ftmClock = F_TIMER; // Set variable for the actual timer clock frequency
  }
#endif

  
  for (prescale = 0; prescale < 7; prescale++) {
    minfreq = (float)(ftmClock >> prescale) / 65536.0f; //Use ftmClock instead of F_TIMER
    if (frequency >= minfreq) break;
  }
  //serial_print("F_TIMER/ftm_Clock = ");
  //serial_phex32(ftmClock >> prescale);
  //serial_print("\n");
  //serial_print("prescale = ");
  //serial_phex(prescale);
  //serial_print("\n");
  mod = (float)(ftmClock >> prescale) / frequency - 0.5f; //Use ftmClock instead of F_TIMER
  if (mod > 65535) mod = 65535;
  //serial_print("mod = ");
  //serial_phex32(mod);
  //serial_print("\n");
  if (pin == FTM1_CH0_PIN || pin == FTM1_CH1_PIN) {
    //FTM1_SC = 0;
    //FTM1_CNT = 0;
    FTM1_MOD = mod;
    FTM1_SC = FTM_SC_CLKS(ftmClockSource) | FTM_SC_PS(prescale);  //Use ftmClockSource instead of 1
  } else if (pin == FTM0_CH0_PIN || pin == FTM0_CH1_PIN
    || pin == FTM0_CH2_PIN || pin == FTM0_CH3_PIN
    || pin == FTM0_CH4_PIN || pin == FTM0_CH5_PIN
#ifdef FTM0_CH6_PIN
    || pin == FTM0_CH6_PIN || pin == FTM0_CH7_PIN
#endif
    ) {
    //FTM0_SC = 0;
    //FTM0_CNT = 0;
    FTM0_MOD = mod;
    FTM0_SC = FTM_SC_CLKS(ftmClockSource) | FTM_SC_PS(prescale);  //Use ftmClockSource instead of 1
  }
#ifdef FTM2_CH0_PIN
    else if (pin == FTM2_CH0_PIN || pin == FTM2_CH1_PIN) {
    //FTM2_SC = 0;
    //FTM2_CNT = 0;
    FTM2_MOD = mod;
    FTM2_SC = FTM_SC_CLKS(ftmClockSource) | FTM_SC_PS(prescale);  //Use ftmClockSource instead of 1
  }
#endif
#ifdef FTM3_CH0_PIN
    else if (pin == FTM3_CH0_PIN || pin == FTM3_CH1_PIN
    || pin == FTM3_CH2_PIN || pin == FTM3_CH3_PIN
    || pin == FTM3_CH4_PIN || pin == FTM3_CH5_PIN
    || pin == FTM3_CH6_PIN || pin == FTM3_CH7_PIN) {
    //FTM3_SC = 0;
    //FTM3_CNT = 0;
    FTM3_MOD = mod;
    FTM3_SC = FTM_SC_CLKS(ftmClockSource) | FTM_SC_PS(prescale);  //Use the new ftmClockSource instead of 1
  }
#endif
#ifdef TPM1_CH0_PIN
    else if (pin == TPM1_CH0_PIN || pin == TPM1_CH1_PIN) {
    //TPM1_SC = 0;
    //TPM1_CNT = 0;
    TPM1_MOD = mod;
    TPM1_SC = FTM_SC_CLKS(ftmClockSource) | FTM_SC_PS(prescale);
  }
#endif
}
*/
