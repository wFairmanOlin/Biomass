#include "Arduino.h"
#include "WBLE.h"
#include <ArduinoBLE.h>


//declare BLE strcutures
BLEService sensorService("19B10010-E8F2-537E-4F6C-D104768A4444");
BLEFloatCharacteristic battery_char("BA77", BLERead | BLENotify);
BLEByteCharacteristic charge_char("501A", BLERead | BLENotify);
BLEByteCharacteristic sd_char("FA71", BLERead | BLENotify);
BLEUnsignedLongCharacteristic time_char ("C10C", BLERead | BLENotify);
BLEUnsignedLongCharacteristic file_char ("515E", BLERead | BLENotify);
BLEIntCharacteristic sensor_on_char("D111", BLERead | BLENotify);
BLEIntCharacteristic sensor_off_char("D000", BLERead | BLENotify);

WBLE::WBLE(void)
{

} 


int WBLE::init(void){
  // begin bluetooth initialization
  if(!BLE.begin()){
    return 0;
  }
  //set bluetooth device name
  BLE.setDeviceName("Biomass Sensor Alpha");
  BLE.setLocalName("BS_A");
  // set the UUID for the service this peripheral advertises:
  BLE.setAdvertisedService(sensorService);
  // add the characteristics to the service
  sensorService.addCharacteristic(sd_char);
  sensorService.addCharacteristic(file_char);
  sensorService.addCharacteristic(battery_char);
  sensorService.addCharacteristic(charge_char);
  sensorService.addCharacteristic(time_char);
  sensorService.addCharacteristic(sensor_on_char);
  sensorService.addCharacteristic(sensor_off_char);
  //initialize service
  BLE.addService(sensorService);
  sd_char.writeValue(0);
  charge_char.writeValue(0);
  file_char.writeValue(0);
  battery_char.writeValue(0);
  time_char.writeValue(0);
  sensor_on_char.writeValue(0);
  sensor_off_char.writeValue(0);
  // start advertising
  BLE.advertise();
  return 1;
}

int WBLE::get_updates(void){
  //poll BLE
  BLE.poll();
  BLEDevice central = BLE.central();
  if(central){
    return 1;
  }
  return 0;
}

void WBLE::update_batt(float new_value){
  battery_char.writeValue(new_value);
}

void WBLE::update_sensor_on(int new_value){
  sensor_on_char.writeValue(new_value);
}

void WBLE::update_sensor_off(int new_value){
  sensor_off_char.writeValue(new_value);
}

void WBLE::update_sd(int new_value){
  sd_char.writeValue(new_value);
}

void WBLE::update_charge(int new_value){
  charge_char.writeValue(new_value);
}

void WBLE::update_file_size(unsigned long new_value){
  file_char.writeValue(new_value);
}

void WBLE::update_time(unsigned long new_value){
  time_char.writeValue(new_value);
}
