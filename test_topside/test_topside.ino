#include <Wire.h>

void setup() {
  // put your setup code here, to run once:
  Wire.begin();
  Serial.begin(115200);
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(5000);
  Serial.println("Sending Transmission");
  Wire.beginTransmission(31);
  Wire.write(2);
  Wire.endTransmission();
  delay(1000);
  Wire.requestFrom(31, 4);
  if(Wire.available() == 4){
    Serial.println(Wire.read());
    Serial.println(Wire.read());
    Serial.println(Wire.read());
    Serial.println(Wire.read());
  }
 
  
}
