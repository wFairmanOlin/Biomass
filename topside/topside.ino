
/*
 * LoRa Receiving Station for Biomass Project
 * Acts as a LoRa server
 * Designed for Heltec Wifi-LoRa 32 V2 Board
 * Driver: RH_RF95
 * Manager: RHReliableDatagram
 */

#include <SPI.h>
#include <RH_RF95.h>
#include <RHReliableDatagram.h>

//for feather32u4 
//#define RFM95_CS 8
//#define RFM95_RST 4
//#define RFM95_INT 7
//#define LED 13

//for HELTEC LORA
#define RFM95_CS 18
#define RFM95_RST 14
#define RFM95_INT 26
#define LED 25

#define SERVER_ADDRESS 1
#define CLIENT_ADDRESS 2

//Set Frequency
#define RF95_FREQ 915.0

// Singleton instance of the radio driver
RH_RF95 driver(RFM95_CS, RFM95_INT);
// Class to manage message delivery and receipt
RHReliableDatagram manager(driver, SERVER_ADDRESS);


void setup() 
{
  pinMode(LED, OUTPUT);
  pinMode(RFM95_RST, OUTPUT);
  Serial.begin(115200);
  delay(100);
  Serial.println("I am alive!");
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
  driver.setSpreadingFactor(10);
  driver.setSignalBandwidth(125000);
//  breaks esp32 boards  
  driver.setFrequency(RF95_FREQ);

  driver.setTxPower(23, false);
  Serial.println("Setup is a Success!");
}


uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{
  if (manager.available())
  {
    // Should be a message for us now
    uint8_t len = sizeof(buf);
    uint8_t from;
    if (manager.recvfromAck(buf, &len, &from))
    {
      //print stats
      digitalWrite(LED, HIGH);
//      Serial.print("\ngot request from : 0x");
//      Serial.print(from, HEX);
//      Serial.print("\nRSSI: ");
//      Serial.print(driver.lastRssi(), DEC);
//      Serial.print("  Freq Error: ");
//      Serial.println(driver.frequencyError(), DEC);

      //handle status messages
      if((buf[0] == 1)){
        //check length
        if(len == 3){
          float battery_voltage = (buf[1] << 8 | buf[2]) * 6.6 / 1024;
          Serial.print("from "); Serial.print(from);
          Serial.print(" status");
          Serial.print(" batt_v "); Serial.print(battery_voltage);
          Serial.print(" RSSI "); Serial.print(driver.lastRssi(), DEC);
          Serial.print(" freqError "); Serial.println(driver.frequencyError(), DEC);
        }
        else
          Serial.println("Status Message Mismatch!");
      }

      //handle data messages
      if(buf[0] == 2){
        //check length
        if(len == 8){
          //check stale data
          if(buf[1] == 1){
            Serial.print("from "); Serial.print(from);
            Serial.print(" data");
            for(int i = 2; i < len; i += 2){
              Serial.print(" ");
              int val = (buf[i] << 8) | buf[i + 1];
              Serial.print(val);
            }
            Serial.println();
          }
          else
            Serial.println("Sensor Data did not Update!");
        }
        else
          Serial.println("Data Message Length Mismatch!");
      }
    }
  }
}
