#include <Wire.h>


#define LED A0
#define DIODE A1
#define LASER 4

/*
 * Make Sure to Burn Bootloader before trying program a new board!
 */
void setup() {
  //set pinmodes
  pinMode(LED, OUTPUT);
  pinMode(LASER, OUTPUT);
  pinMode(DIODE, INPUT);
  digitalWrite(LED, HIGH);

  //setup i2c
  Wire.begin(1);
  Wire.onRequest(requestEvent);


}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(LED, LOW);
  digitalWrite(LASER, LOW);
  delay(500);
  digitalWrite(LED, HIGH);
  digitalWrite(LASER, HIGH);
  int voltage = analogRead(DIODE);
  delay(500);
}

void requestEvent(int cmd) {
  if (cmd == 2) {
    int v_low = analogRead(DIODE);
    digitalWrite(LED, HIGH);
    digitalWrite(LASER, HIGH);
    delay(500);
    int v_high = analogRead(DIODE);
    delay(500);
    digitalWrite(LASER, LOW);
    digitalWrite(LED, LOW);
  }
  else {
    for (int i = 0; i < 50; i ++){
      digitalWrite(LED, HIGH);
      delay(25);
      digitalWrite(LED, LOW);
      delay(25);
    }
  }
}
