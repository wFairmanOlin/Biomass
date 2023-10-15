
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
#define RFM95_CS 8
#define RFM95_RST 4
#define RFM95_INT 7
#define LED 13

//for HELTEC LORA
//#define RFM95_CS 18
//#define RFM95_RST 14
//#define RFM95_INT 26
//#define LED 25

#define SERVER_ADDRESS 1

//Set Frequency
#define RF95_FREQ 915.0

// Singleton instance of the radio driver
RH_RF95 driver(RFM95_CS, RFM95_INT);
// Class to manage message delivery and receipt
RHReliableDatagram manager(driver, SERVER_ADDRESS);

union Data {
  int i;
  float f;
  uint8_t bytes[4];
};


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
  driver.setSpreadingFactor(12);
  driver.setSignalBandwidth(125000);
//  breaks esp32 boards  
  driver.setFrequency(RF95_FREQ);

  driver.setTxPower(23, false);
  Serial.println("Setup is a Success!");
}


uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];

void loop()
{
    // Serial.println("Message available for processing.");

    if (manager.available())
    {
        // Should be a message for us now
        uint8_t len = sizeof(buf);
        uint8_t from;
        
        if (manager.recvfromAck(buf, &len, &from))
        {
            Serial.println("Message received successfully.");

            digitalWrite(LED, HIGH);

            //handle status messages
            if((buf[0] == 1)){
                if(len == 3){
                    float battery_voltage = buf[1] * 6.6 / 256; // Using only MSB
                    Serial.print("from "); Serial.print(from);
                    Serial.print(" status");
                    Serial.print(" batt_v "); Serial.print(battery_voltage);
                    Serial.print(" RSSI "); Serial.print(driver.lastRssi(), DEC);
                    Serial.print(" freqError "); Serial.println(driver.frequencyError(), DEC);
                }
                else
                    Serial.println("Status Message Mismatch!"); Serial.println(buf[0]);
            }

            //handle data messages
            if(buf[0] == 2){
                if(len == 8){
                    if(buf[1] == 1){
                        Serial.print("from "); Serial.print(from);
                        Serial.print(" data");
                        for(int i = 2; i < len; i += 2){
                            Serial.print(" ");
                            int val = buf[i]; // Using only MSB
                            Serial.print(val);
                        }
                        Serial.println();
                    }
                    else
                        Serial.println("Sensor Data did not Update!");
                }
                else
                    Serial.println("Data Message Length Mismatch!"); Serial.println(buf[0]);
            }

            //handle gps messages
            if(buf[0] == 3){
                if(len == 9){
                    int idx = 1;
                    union Data lat, lng;
                    lat.bytes[0] = buf[idx++]; // Only MSB
                    idx+=3; // Skip other bytes
                    lng.bytes[0] = buf[idx++]; // Only MSB
                    Serial.print("from 100");  
                    Serial.print(" lat "); Serial.print(lat.f, 6);
                    Serial.print(" lng "); Serial.print(lng.f, 6);
                    Serial.print(" RSSI "); Serial.print(driver.lastRssi(), DEC);
                    Serial.println(buf[0]);
                }
        }

      //handle fast data
      if(buf[0] == 4){
        //check length
        //check length
        if(len == 103){
            Serial.print("from "); Serial.print(from);
            Serial.print(" fdata ");
            Serial.print(buf[1]); Serial.print(" of "); Serial.print(buf[2]);
            for(int i = 3; i < len; i++){  // Adjusted loop to process one byte at a time
                Serial.print(" ");
                int val = buf[i];  // Using only MSB
                Serial.print(val);
            }
            Serial.println();
        }
        else {
            Serial.println("Fast Data Message Length Mismatch!");
            Serial.println(buf[0]);
          }
      }
    }
  }
}

