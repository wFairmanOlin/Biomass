#ifndef WBLE_h
#define WBLE_h

#include "Arduino.h"
#include "mbed.h"
#include <ArduinoBLE.h>

class WBLE
{
  public:
  char current_central[19] = "00:00:00:00:00:00\0";
  char user_central[19] = "00:00:00:00:00:00\0";
  char no_addr[19] = "00:00:00:00:00:00\0"; 
    
    WBLE(void);
    int init(void);
    int get_updates(void);
    void update_batt(float new_value);
    void update_sensor_on(int new_value);
    void update_sensor_off(int new_value);
    void update_sd(int new_value);
    void update_time(unsigned long new_value);
    void update_file_size(unsigned long new_value);
    void update_charge(int new_value);
};

#endif
