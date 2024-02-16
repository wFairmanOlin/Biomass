#include <Wire.h>
#include <avr/sleep.h>
#include <avr/wdt.h>

/*
   Make Sure to Burn Bootloader before trying program a new board!
*/
#define I2C_ADDRESS 1
#define LED A0
#define DIODE A1
#define LASER 4

int state = 0;
int counter = 0;
uint8_t data[10];


void setup() {
  //set pinmodes
  wdt_reset();
  wdt_enable(WDTO_2S);
  pinMode(LED, OUTPUT);
  pinMode(LASER, OUTPUT);
  pinMode(DIODE, INPUT);

  //setup i2c
  Wire.begin(I2C_ADDRESS);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);

  for (int i = 0; i < 2; i ++){
    digitalWrite(LED, HIGH);
    delay(50);
    digitalWrite(LED, LOW);
    delay(50);
  }
  
}


/**
 * State Machine
 * 
 * State 0 -> go to deep sleep
 * State 1 -> sample ADC
 * State 2 -> turn on laser
 * State 3 -> turn off laser
 * State 4 -> turn on green led
 * State 5 -> turn off green led
 * 
 */
 
void loop() {
  switch (state) {

    case 1:
      wdt_reset();
      takeSingleSample();
      //request ADC data to leave state 1
      break;

    case 2:
      wdt_reset();
      digitalWrite(LASER, HIGH);
      state = 0;
      break;

    case 3:
      wdt_reset();
      digitalWrite(LASER, LOW);
      state = 0;
      break;

    case 4:
      wdt_reset();
      digitalWrite(LED, HIGH);
      state = 0;
      break;

    case 5:
      wdt_reset();
      digitalWrite(LED, LOW);
      state = 0;
      break;
      
    default:
      break;
  }
}

void requestEvent() {
  if (state == 1) {
    Wire.write(data, 2);
    state = 0;
  }
}

void receiveEvent(int howMany) {
  if (howMany == 1) {
    state =  Wire.read();
  }
}

void takeSample(int samples) {
  uint32_t sample_val = 0;

  for (int i = 0; i < samples; i ++) {
    delayMicroseconds(100);
    sample_val += analogRead(DIODE);
  }
  
  sample_val /= samples;

  data[0] = (sample_val >> 8) & 0xFF;
  data[1] = sample_val & 0xFF;
}

void takeSingleSample(){
  uint32_t sample_val = analogRead(DIODE);
  data[0] = (sample_val >> 8) & 0xFF;
  data[1] = sample_val & 0xFF;
}

//void takeSample(int samples) {
//  uint32_t local_off = 0;
//  uint32_t local_on = 0;
//
//  digitalWrite(LASER, LOW);
//  digitalWrite(LED, LOW);
//  for (int i = 0; i < samples; i ++) {
//    local_off += analogRead(DIODE);
//  }
//  digitalWrite(LASER, HIGH);
//  digitalWrite(LED, HIGH);
//  delay(500);
//  for (int i = 0; i < samples; i ++) {
//    local_on += analogRead(DIODE);
//  }
//  digitalWrite(LASER, LOW);
//  digitalWrite(LED, LOW);
//  local_off /= samples;
//  local_on /= samples;
//
//  data[0] = (local_off >> 8) & 0xFF;
//  data[1] = local_off & 0xFF;
//  data[2] = (local_on >> 8)  & 0xFF;
//  data[3] = local_on & 0xFF;
//}
