#include <Wire.h>

/*
 * Make Sure to Burn Bootloader before trying program a new board!
 */

#define LED A0
#define DIODE A1
#define LASER 4

int state = 0;
uint8_t data[4];

void setup() {
  //set pinmodes
  pinMode(LED, OUTPUT);
  pinMode(LASER, OUTPUT);
  pinMode(DIODE, INPUT);
  digitalWrite(LED, HIGH);

  //setup i2c
  Wire.begin(31);
  Wire.onRequest(requestEvent);
  Wire.onReceive(receiveEvent);
  delay(5000);
  digitalWrite(LED, LOW);


}

void loop() {
  if (state == 1){
    takeSample(10);
    state = 2;
  }
}

void requestEvent() {
  if (state == 2) {
    Wire.write(data, 4);
    state = 0;
  }
}

void receiveEvent(int howMany){
  if (howMany == 1){
    int cmd = Wire.read();
    if (cmd == 2)
      state = 1;
  }
}

void takeSample(int samples){
  uint32_t local_off = 0;
  uint32_t local_on = 0;
  
  digitalWrite(LASER, LOW); 
  for(int i = 0; i < samples; i ++){
    local_off += analogRead(DIODE);
  }
  digitalWrite(LASER, HIGH);
  delay(100);
  for(int i = 0; i < samples; i ++){
    local_on += analogRead(DIODE);
  }
  digitalWrite(LASER, LOW);
  local_off /= samples;
  local_on /= samples;

  local_off = 0;
  local_on = 121;

  data[0] = local_off >> 8;
  data[1] = local_off;
  data[3] = local_on >> 8;
  data[4] = local_on;
}
