#include <SPI.h>
#include <SD.h>
#include "WBLE.h"

int gb_a[] = {1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1};
int gb_b[] = {1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,0};
float output[32];

int *gba_ptr = &gb_a[0];
int *gbb_ptr = &gb_b[0];
float *out_ptr = &output[0];

//counter variables
const unsigned long day_sec = 86400;//num of secs in day check
unsigned long sec_counter = 0;     //num of secs since system on
unsigned long prev_sample = 0;     //keep track of secs since last meas
unsigned long prev_update = 0;     //keep track of secs since last update
unsigned long prev_poll = 0;                 //keep track of BLE polling
unsigned long previous_millis = 0; //keep track of millis for sec update
unsigned long minutes_on = 0;      //num of mins since system on
int day_counter = 0;               //num of days since system on
unsigned long millis_leftover = 0; //extra millis

//flags
int sd_on = 0;
int writing = 0;
int central_connected = 0;



File file;

WBLE ble; 

void setup() {
  pinMode(D2, OUTPUT);
  pinMode(A0, INPUT);
  pinMode(A7, INPUT);
  pinMode(A1, INPUT_PULLUP);
  digitalWrite(D2, 0); //set laser off
  Serial.begin(9600);
  ble.init();
  delay(1000);
  sd_init();
  delay(2000);
  digitalWrite(D2, 1); delay(50); 
  ble.update_sensor_on(measure_diode(200));
  digitalWrite(D2, 0); delay(50); 
  ble.update_sensor_off(measure_diode(200));
  ble.update_batt(readBatteryVoltage());
  
}

void loop() {
  //update BLE
  if((millis() - prev_poll) > 10){
    central_connected = ble.get_updates();
    prev_poll = millis();
  }
  
  //sec counter - check
  if((millis() - previous_millis) > 1000){
    unsigned long millis_diff = (millis() - previous_millis); 
    sec_counter += millis_diff / 1000;
    millis_leftover +=  millis_diff % 1000;
    previous_millis = millis();
  }

  //minute counter - check
  if(sec_counter - prev_update > 60){
    prev_update = sec_counter;
    //check if there are leftover millis
    if(millis_leftover >= 1000){
      sec_counter += 1;
      millis_leftover = 0;
    }
    minutes_on ++;
    //update ble only if central device is connected
    if(central_connected){
      ble.update_time(minutes_on);
      digitalWrite(D2, 1); delay(50);
      ble.update_batt(readBatteryVoltage());
      ble.update_sensor_on(measure_diode(10));
      digitalWrite(D2, 0); delay(50); 
      ble.update_sensor_off(measure_diode(10));
    }
  }
  
  //day counter
  if(sec_counter >= day_sec){
    sec_counter = 0;
    prev_update = 0;
    prev_sample = day_sec - prev_sample;
    day_counter += 1;
  }

   //take a measurement every 15 mins - check
  if(sd_on){
    if(sec_counter - prev_sample > 900){
        prev_sample = sec_counter;
        golay_seq_sd(gba_ptr, out_ptr, 32); //run 1st seq
        digitalWrite(D2, 0);
        delay(50);
        golay_seq_sd(gbb_ptr,out_ptr, 32); //run 2nd sequence

        //log measurement and battery voltage
        file = SD.open("log.csv", FILE_WRITE);
        file.print(day_counter); file.print(","); file.print(sec_counter);
        file.println(",measurement,");
        file.print(day_counter); file.print(","); file.print(sec_counter);
        file.print(",battery,"); file.println(readBatteryVoltage());
        file.print(day_counter); file.print(","); file.print(sec_counter);
        file.print(",charging,"); file.println(isCharging());
        file.close();
    }
  }

  switch(Serial.read()){
  case 'r':
    sd_on = 1;
    prev_sample = 59;
    break;
  case 'd':
    day_counter = Serial.parseInt();
    break;
  case 't':
    sec_counter = Serial.parseInt();
    break;
  case 'v':
    Serial.print("\nsd status: "); Serial.println(sd_on);
    digitalWrite(D2, 1); delay(50);
    file = SD.open("golaySeq.csv");
    Serial.print("file size: "); Serial.println(file.size()); file.close();
    Serial.print("sensor on: ");   Serial.println(measure_diode(200));
    digitalWrite(D2, 0); delay(50);
    Serial.print("sensor off: ");  Serial.println(measure_diode(200));
    Serial.print("battery v: ");   Serial.println(readBatteryVoltage());
    Serial.print("Charging Status: "); Serial.println(isCharging());
    Serial.print("secs: ");        Serial.println(sec_counter);
    Serial.print("minutes: ");     Serial.println(minutes_on);
    Serial.print("day: ");         Serial.println(day_counter);
    
    break;
  case 'z':
    SD.remove("golaySeq.csv");
    Serial.println("Removing Files");
    sd_on = 0;
    break;
  default: 
  break;
  }
}

void sd_init(void){

  if(!SD.begin()){
    Serial.println("SD Failed Init");
  }

  //init sd and make files
  else{
    Serial.println("SD init success!");
    sd_on = 1;
    ble.update_sd(sd_on);
    if(!SD.exists("golaySeq.csv")){
      Serial.println("Making golaySeq.csv");
      file = SD.open("golaySeq.csv", FILE_WRITE);
      file.println("day,sec,name,value");
      file.close();
    }
    
   if(!SD.exists("log.csv")){
      Serial.println("Making log.csv");
      file = SD.open("log.csv", FILE_WRITE);
      file.println("day,sec,event,value");
      file.close();
    }

    //note system startup in log file
    file = SD.open("log.csv", FILE_WRITE);
    file.println("0,0,system on,");
    file.println("0,0,battery,");
    file.println(readBatteryVoltage());
    file.close();
  }
  
}

int measure_diode(int sample_len){
  unsigned long reading = 0;

  for(int i = 0; i < sample_len; i++){
    reading += analogRead(A7);
  }
  return reading / sample_len;
}

void golay_seq_sd(int *in, float *out, int len){
  file = SD.open("golayseq.csv", FILE_WRITE);
  for(int i = 0; i < len; i ++){
    digitalWrite(D2, *(in + i));
    
    //delay between each golay value
    delay(50);
    *(out + i) = measure_diode(200);
  }
   file.print(day_counter); file.print(','); 
   file.print(sec_counter); file.print(',');
   file.print("add,");
   file.println((unsigned int)in);
   for(int i = 0; i < len; i ++){
     file.print(day_counter);    file.print(','); 
     file.print(sec_counter);    file.print(',');
     file.print((int)*(in + i)); file.print(",");
     file.println((float)*(out + i));
   }
  file.flush();
  ble.update_file_size(file.size());
  file.close();
}

float readBatteryVoltage(void){
  float reading = 0;
  for(int i = 0; i < 50; i++){
    reading += analogRead(A0);
  }
  return reading * 6.6 / 1024 / 50;
}

int isCharging(void){
  if(analogRead(A1) < 500){
    ble.update_charge(1);
    return 1;
  }
  ble.update_charge(0);
  return 0;
}
