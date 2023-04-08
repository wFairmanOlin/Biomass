#include <Wire.h>

uint8_t data_message[8];

/* Buffers */
long ga[] = {1,1,1,-1,1,1,-1,1,1,1,1,-1,-1,-1,1,-1,1,1,1,-1,1,1,-1,1,-1,-1,-1,1,1,1,-1,1};
long gb[] = {1,1,1,-1,1,1,-1,1,1,1,1,-1,-1,-1,1,-1,-1,-1,-1,1,-1,-1,1,-1,1,1,1,-1,-1,-1,1,-1};

long golay_a_buffer[32];
long golay_b_buffer[32];


void setup() {
  // put your setup code here, to run once:
  Wire.begin();
  Serial.begin(115200);
}

void loop() {
  // put your main code here, to run repeatedly:
  data_message[1] = get_data();
  Serial.print("\nMessage Received: ");
  Serial.println(data_message[1]);
  Serial.print("off: ");
  Serial.println((data_message[2] << 8) | data_message[3]);
  Serial.print("on: ");
  Serial.println((data_message[4] << 8) | data_message[5]);
  delay(1000); 
  data_message[1] = get_golay(0);
  Serial.println("\nGolay Received: ");
  Serial.println(data_message[1]);
  Serial.print("golay: ");
  Serial.println((data_message[6] << 8) | data_message[7]);
  send_cmd(4, 5);
  send_cmd(2, 5);
  delay(5000);
  
}

void send_cmd(int cmd, int d_val){
  Wire.beginTransmission(1);
  Wire.write(cmd);
  Wire.endTransmission(1);
  delay(d_val);
}

/**
 * State Machine for Receiver
 * 
 * State 0 -> go to deep sleep
 * State 1 -> sample ADC
 * State 2 -> turn on laser
 * State 3 -> turn off laser
 * State 4 -> turn on green led
 * State 5 -> turn off green led
 * 
 */
int get_data(){
  //wake up device
  Wire.beginTransmission(1);
  Wire.endTransmission();
  delay(5);
  //make sure laser is off
  send_cmd(3, 5);
  //sample ADC
  send_cmd(1, 25);
  Wire.requestFrom(1,2);
  if(Wire.available() == 2){
    data_message[2] = Wire.read();
    data_message[3] = Wire.read();
  }
  else
    return 0;
  delay(5);
  //turn on laser
  send_cmd(2, 50);
  //sample ADC
  send_cmd(1, 25);
  Wire.requestFrom(1,2);
  if(Wire.available() == 2){
    data_message[4] = Wire.read();
    data_message[5] = Wire.read();
  }
  else{
    //try to turn off laser if issues with ADC
    send_cmd(3, 5);
    return 0;
  }
  delay(5);
  //turn off laser
  send_cmd(3, 5);
  return 1;
}



 /*
 * Perform a golay calculation
 * d_val: delay time in milliseconds
 */
int get_golay(int d_val){
  //fill golay_a sequence
  long ga_mean = 0;
  for (int i = 0; i < sizeof(ga) / 4; i ++){
    //abort if get_data fails
    delay(d_val);
    if (get_data() == 0)
      return 0;
    //store data
    if (ga[i] == 1){
      golay_a_buffer[i] = (data_message[4] << 8) | (data_message[5]);
    } else {
      golay_a_buffer[i] = (data_message[2] << 8) | (data_message[3]);
    }
    ga_mean += golay_a_buffer[i];   
  }
  ga_mean /= 32;
  
  //fill golay_b sequence
  long gb_mean = 0;
  for (int i = 0; i < sizeof(gb) / 4; i ++){
    //abort if get_data fails
    delay(d_val);
    if (get_data() == 0)
      return 0;
    //store data
    if (gb[i] == 1){
      golay_b_buffer[i] = (data_message[4] << 8) | (data_message[5]);
    } else {
      golay_b_buffer[i] = (data_message[2] << 8) | (data_message[3]);
    }
    gb_mean = golay_b_buffer[i];   
  }
  gb_mean /= 32;
  
  //perform cross_correlation
  int results = 0;
  for(int i = 0; i < sizeof(ga) / 4; i ++){
    long xa = (golay_a_buffer[i] - ga_mean) * ga[i];
    long xb = (golay_b_buffer[i] - gb_mean) * gb[i];
    results += xa + xb;
  }
  
  Serial.print("Results ");
  Serial.println(results);
  data_message[6] = (results >> 8) & 0xFF;
  data_message[7] = (results) & 0xFF;
  return 1;
}
