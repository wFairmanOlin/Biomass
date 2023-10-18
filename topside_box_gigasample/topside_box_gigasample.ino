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

#define SERVER_ADDRESS 1
#define CLIENT_ADDRESS 4 //sensor id + 1 (i know, this should change)

//Set Frequency
#define RF95_FREQ 915.0

//Schedule Updates in Minutes
#define UPDATE_FREQ 5

// Singleton instance of the radio driver
RH_RF95 driver(RFM95_CS, RFM95_INT);
// Class to manage message delivery and receipt
RHReliableDatagram manager(driver, CLIENT_ADDRESS);

uint8_t status_message[3];
uint8_t data_message[600];  // Updated size

/* COUNTERS */
unsigned long prev_update = 0;

/* Watchdog Timer for Low Power Mode*/
int wdt_counter = 0;
int status_counter = 0;
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

  manager.setTimeout(5000);
  driver.setSpreadingFactor(12);
  driver.setSignalBandwidth(125000);
  driver.setFrequency(RF95_FREQ);
  driver.setTxPower(23, false);
  digitalWrite(LED, HIGH);
  delay(5000);
  digitalWrite(LED, LOW);
  delay(500);
}

//for receiving messages
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{
  int wdt_limit = UPDATE_FREQ * 60 / 8;
  if (wdt_counter >= wdt_limit){
    wdt_counter = 0;
    send_status();
    send_data();
    driver.sleep(); //powers down radio module. Has time delay for starting up again
    digitalWrite(LED, LOW);
  }

  wdt_counter++;
  //configure watchdog timer to go off in 1 second
  WDTCSR = bit(WDCE) | bit(WDE);
  WDTCSR = bit(WDIE) | bit(WDP3) | bit(WDP0);
  wdt_reset();

  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  sleep_cpu();
  sleep_disable();
}

void send_status() {
  int vbat = read_battery();
  status_message[0] = 1;
  status_message[1] = vbat >> 8;
  status_message[2] = vbat;

  if (manager.sendtoWait(status_message, sizeof(status_message), SERVER_ADDRESS))
    Serial.println("Status Message Acknowledged");
  else
    Serial.println("Status Message Not Received");
}

void send_data() {
  for (int i = 0; i < sizeof(data_message); i++) {
    get_data(i);
  }

  // Print the data_message contents to the serial monitor
  for (int i = 0; i < sizeof(data_message); i++) {
    Serial.println(data_message[i]);
  }

  int msg_type = 5;
  int msg_size = 100;
  int msg_count = sizeof(data_message) / msg_size;
  uint8_t temp_data[msg_size + 3];
  for (int i = 1; i <= msg_count; i++) {
    temp_data[0] = msg_type;
    temp_data[1] = i;
    temp_data[2] = msg_count;
    for (int idx = 0; idx < msg_size; idx++) {
      temp_data[idx + 3] = data_message[(i - 1) * msg_size + idx];
    }
    Serial.println();

    if (manager.sendtoWait(temp_data, sizeof(temp_data), SERVER_ADDRESS)) {
      Serial.print("Data Message ");
      Serial.print(i);
      Serial.print("/");
      Serial.print(msg_count);
      Serial.println(" Received");
    } else {
      Serial.print("Data Message ");
      Serial.print(i);
      Serial.print("/");
      Serial.print(msg_count);
      Serial.println(" NOT Received");
    }
  }
}

void send_cmd(int cmd, int d_val) {
  Wire.beginTransmission(1);
  Wire.write(cmd);
  Wire.endTransmission(1);
  delay(d_val);
}

int get_data(int count) {
  int val = 0;

  send_cmd(1, 8); 
  Wire.requestFrom(1, 2);
  if (Wire.available() == 2) {
    val = (Wire.read() << 8) | Wire.read();
  }

  uint8_t msbs = 0xFF & (val >> 2);
  data_message[count] = msbs;

  return 1;
}

int read_battery() {
  int measured_vbat = 0;
  for (int i = 0; i < 10; i++) {
    measured_vbat += analogRead(BATT_PIN);
  }
  Serial.print("Batt V ");
  float vbat_f = measured_vbat / 10 * 6.6 / 1024;
  Serial.println(vbat_f);
  return measured_vbat / 10;
}
