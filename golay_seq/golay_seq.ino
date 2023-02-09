#include <SPI.h>
#include <SD.h>
#include "mbed.h"

int gb_a[] = {1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,1,1,1,0,1,1,0,1,0,0,0,1,1,1,0,1};
int gb_b[] = {1,1,1,0,1,1,0,1,1,1,1,0,0,0,1,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,0};
float output[32];

int *gba_ptr = &gb_a[0];
int *gbb_ptr = &gb_b[0];
float *out_ptr = &output[0];



mbed::Timer clock_timer;


//counter variables
const unsigned long day_millis =  86400000;
unsigned long mill_counter = 0;
int day_counter = 0;

//flags
int record = 0;

unsigned long previous = millis();

File myFile;

void setup() {

  pinMode(D2, OUTPUT);
  digitalWrite(D2, 0); //set laser off
  Serial.begin(115200);
  while(!Serial){}//wait for serial startup
  sd_init();
}

void count(){
  day_counter += 1;
}

void loop() {

  if(clock_timer.read() > 0.0001){
    day_counter += round(clock_timer.read() * 1000);
    clock_timer.reset();
  }
  
  switch(Serial.read()){
  
  case 's':
   sample();
   break;
  case 'r':
    record = 1;
    break;
  case 'd':
    day_counter = Serial.parseInt();
    break;
  case 't':
    mill_counter = Serial.parseInt();
    break;
  case 'v':
    Serial.print("day: ");
    Serial.println(day_counter);
    Serial.print("mill_counter: ");
    Serial.println(mill_counter);
    Serial.println(clock_timer.read());

  if(record){
    //nothing
  }
  }
}

void sd_init(void){

  if(!SD.begin()){
    Serial.println("SD Failed Init");
  }
  else{
    Serial.println("SD init success!");
  }

  if(!SD.exists("golay_seq.csv")){
    Serial.println("Making golay_seq.csv");
    myFile = SD.open("golay_seq.csv", FILE_WRITE);
    myFile.println("time,name,value");
    myFile.close();
  }
    
   if(!SD.exists("binary.csv")){
    Serial.println("Making binary.csv");
    myFile = SD.open("binary.csv", FILE_WRITE);
    myFile.println("time,name,value");
    myFile.close();
  }
}

void sample(){

    int reading = 900;
    int reading2 = 760;
    Serial.println((float)reading);
    Serial.println((float)reading2);

//    //take golay readings
//    for(int i=0; i < 10; i++){
//    //run first sequence
//    golay_seq(gba_ptr, out_ptr, 32);
//
//    //delay by 100 ms
//    digitalWrite(D2, 0);
//    delay(100);
//
//    //run 2nd sequence
//    golay_seq(gbb_ptr,out_ptr, 32);
//    previous = millis();
//  }

  //take continuous stream readings
  while(Serial.read() != 's'){
    if ((millis() - previous) > 100){
  
  
        digitalWrite(D2, 1);
        delay(10);
        Serial.print("1,");
        Serial.print(measure_diode(100));
        Serial.print(",");
        digitalWrite(D2, 0);
        delay(10);
        Serial.print("0,");
        Serial.println(measure_diode(100));
        previous = millis();
    }
  digitalWrite(D2, 0);
  }  
}


void golay_seq(int *in, float *out, int len){

  for(int i = 0; i < len; i ++){
    digitalWrite(D2, *(in + i));
    
    //delay between each golay value
    delay(2);
    *(out + i) = measure_diode(100);
  }

   Serial.print("add,");
   Serial.println((unsigned int)in);
   for(int i = 0; i < len; i ++){
     Serial.print((int)*(in + i));
     Serial.print(",");
     Serial.println((float)*(out + i));
   }
  Serial.println("golay,stop");
}



float measure_diode(int sample_len){
  float reading = 0;

  for(int i = 0; i < sample_len; i++){
    reading += analogRead(A7);
  }
//  return reading / sample_len;
  return (float)analogRead(A7);
}
