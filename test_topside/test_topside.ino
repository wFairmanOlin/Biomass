#include <Wire.h>

void setup() {
  // put your setup code here, to run once:
  Wire.begin();
  Serial.begin(115200);
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(4000);
  Serial.println("Sending Transmission");
  Wire.beginTransmission(1);
  Wire.endTransmission();
  delay(5);
  Wire.beginTransmission(1);
  Wire.write(2);
  Wire.endTransmission();
  delay(2000);
  Wire.requestFrom(1, 4);
  if(Wire.available() == 4){
//    Wire.read();
//    Wire.read();
//    Wire.read();
//    Wire.read();
    Serial.print("off ");
    Serial.println( (Wire.read() << 8) | Wire.read());
    Serial.print("on ");
    Serial.println( (Wire.read() << 8) | Wire.read());
  }
}
