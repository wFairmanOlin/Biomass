
/*
 * LoRa Transmitting Station for Biomass Project
 * Acts as a LoRa client
 * Designed for Heltec Wifi-LoRa 32 V2 Board
 * Driver: RH_RF95
 * Manager: RHReliableDatagram
 */

#include <SPI.h>
#include <Wire.h>
#include <RH_RF95.h>
#include <RHReliableDatagram.h>
#include <avr/sleep.h> //for low power operations
#include <avr/power.h> //for low power operations
#include <avr/wdt.h>   //for low power operations


// for feather32u4 
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7
#define LED 13
#define BATT_PIN A9


//for HELTEC LORA
//#define RFM95_CS 18
//#define RFM95_RST 14
//#define RFM95_INT 26
//#define LED 25
//#define BATT_PIN 37

#define SERVER_ADDRESS 1
#define CLIENT_ADDRESS 4 //change this

//Set Frequency
#define RF95_FREQ 915.0

//Schedule Updates in Minutes
#define UPDATE_FREQ 20

// Singleton instance of the radio driver
RH_RF95 driver(RFM95_CS, RFM95_INT);
// Class to manage message delivery and receipt
RHReliableDatagram manager(driver, CLIENT_ADDRESS);

/* TEST DATA */
uint8_t test_charging = 0;

/* Buffers */
long ga[] = {1,1,1,-1,1,1,-1,1,1,1,1,-1,-1,-1,1,-1,1,1,1,-1,1,1,-1,1,-1,-1,-1,1,1,1,-1,1};
long gb[] = {1,1,1,-1,1,1,-1,1,1,1,1,-1,-1,-1,1,-1,-1,-1,-1,1,-1,-1,1,-1,1,1,1,-1,-1,-1,1,-1};

uint8_t status_message[3];
uint8_t data_message[8];

long golay_a_buffer[32];
long golay_b_buffer[32];

/* COUNTERS */
unsigned long prev_update = 0;

/* Watchdog Timer for Low Power Mode*/
int wdt_counter = 0;
ISR (WDT_vect){
  wdt_disable(); //end watchdog
}
void setup()
{
  Serial.begin(115200);
  delay(100);
  pinMode(LED, OUTPUT);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  delay(100);
  if (!manager.init())
    Serial.println("init failed");

  /*  MODEM CONFIG IMPORTANT!!!
   *   
   *  Bw125Cr45Sf128   -> Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Default medium range. 
   *  Bw500Cr45Sf128   -> Bw = 500 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Fast+short range. 
   *  Bw31_25Cr48Sf512 -> Bw = 31.25 kHz, Cr = 4/8, Sf = 512chips/symbol, CRC on. Slow+long range.
   *  Bw125Cr48Sf4096  -> Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, low data rate, CRC on. Slow+long range.
   *  Bw125Cr45Sf2048  -> Bw = 125 kHz, Cr = 4/5, Sf = 2048chips/symbol, CRC on. Slow+long range.
   *  
   *  If data rate is slower, increase timeout below
   */
  manager.setTimeout(5000);
//  driver.setModemConfig(RH_RF95::Bw125Cr45Sf2048);
  driver.setSpreadingFactor(12);
  driver.setSignalBandwidth(125000);
  driver.setFrequency(RF95_FREQ);
  driver.setTxPower(23, false);
  digitalWrite(LED, HIGH);
  delay(5000);
  digitalWrite(LED, LOW);
  delay(500);
  send_data();
}

//for receiving messages
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{
  int wdt_limit = UPDATE_FREQ * 60 / 8;
  if (wdt_counter >= wdt_limit){
    wdt_counter = 0;
    //send messages
    delay(CLIENT_ADDRESS); //add unique delay
    digitalWrite(LED, HIGH);
    //status
    send_status();
//    data
    send_data();
    delay(100);
    driver.sleep(); //powers down radio module. Has time delay for starting up again
    digitalWrite(LED, LOW);
    
  }
  //for testing
//  delay(8000);
//  wdt_counter ++;
  /* end of loop handles putting uC to sleep*/
  wdt_counter ++;
  //configure watchdog timer to go off in 8 seconds
  WDTCSR = bit(WDCE) | bit(WDE);
  WDTCSR = bit(WDIE) | bit(WDP3) | bit(WDP0);
  wdt_reset();

  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  sleep_cpu();
  sleep_disable();
}

/**
 * Send status message of sensor which currently only contains battery voltage.
 * message ID: 1
 */
void send_status(){
  //write status message -> message ID 1
  int vbat = read_battery();
  status_message[0] = 1;
  status_message[1] = vbat >> 8;
  status_message[2] = vbat;

  //send status_message
  if (manager.sendtoWait(status_message, sizeof(status_message), SERVER_ADDRESS))
    Serial.println("Status Message Acknowledged");
  else
    Serial.println("Status Message Not Received");
}

/**
 * Send data message from sensor.
 * 1 -> 16 bit laser off diode voltage
 * 2 -> 16 bit laser on diode voltage
 * 3 -> 16 bit golay sequence
 * 
 * message ID: 2
 */
void send_data(){
  data_message[0] = 2;
  data_message[1] = get_golay(0);

  //send data_message
  if (manager.sendtoWait(data_message, sizeof(data_message), SERVER_ADDRESS))
    Serial.println("Data Message Acknowledged");
  else
    Serial.println("Data Message Not Received");
  
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
 * Read Battery Voltage
 */
int read_battery(){
  int measured_vbat = 0;
  for(int i = 0; i < 10; i++){
    measured_vbat += analogRead(BATT_PIN);
  }
  Serial.print("Batt V ");
  float vbat_f = measured_vbat / 10 * 6.6 / 1024;
  Serial.println(vbat_f);
  return measured_vbat / 10;
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
