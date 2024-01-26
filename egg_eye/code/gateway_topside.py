
import os
import time
import subprocess
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
from smbus2 import SMBus, i2c_msg

############### Running On Startup ###############
# To configure this script to run on startup for unix systems
# add a command to the cron scheduler using crontab.
#
# Run "sudo crontab -e" to open the editor
#
# Paste the following line
#
# @reboot /usr/bin/python3 /home/Desktop/Biomass/pc_basestation/gateway.py &>> /home/Desktop/Biomass/pc_basestation/cronlog.log
#
# This runs the program when the device is powered on and stores the output in
# the local "cronlog.log" file. Please note that the python script outputs a more detailed
# log in the local "log.log" file.
#
# Let the computer establish a network connection on reboot
folder = "Desktop/Biomass/pc_basestation/"
# folder = "" #for testing

############### I2C FUNCTIONS ############### 
# State 0 -> go to deep sleep
# State 1 -> sample ADC
# State 2 -> turn on laser
# State 3 -> turn off laser
# State 4 -> turn on green led
# State 5 -> turn off green led

def collect_sample():
    with SMBus(1) as bus:
        bus.write_byte(1,5) # turn off led 
        time.sleep(0.1)
        bus.write_byte(1, 3) # turn off laser
        time.sleep(0.1)
        bus.write_byte(1, 1) # take sample
        time.sleep(0.1)
        msg = i2c_msg.read(1,2) # read sample
        bus.i2c_rdwr(msg)
        msg = list(msg)
        off = (int(msg[0]) << 8) + int(msg[1])
        bus.write_byte(1, 4) # turn on led
        time.sleep(0.1)
        bus.write_byte(1, 2) # turn on laser
        time.sleep(0.25)
        bus.write_byte(1, 1) # take sample
        time.sleep(0.1)
        msg = i2c_msg.read(1,2) # read sample
        bus.i2c_rdwr(msg)
        msg = list(msg)
        on = (int(msg[0]) << 8) + int(msg[1])
        time.sleep(1)
        bus.write_byte(1, 5) # turn off led
        time.sleep(0.1)
        bus.write_byte(1, 3) # turn off laser
        time.sleep(0.1)

    return off, on

        


############### FIREBASE FUNCTIONS ############### 
def restart_firebase(app):
    logging.info('Attempting to restart Firebase Connection')
    firebase_admin.delete_app(app)
    time.sleep(60)
    logging.info('Current IP Address: ' + get_IP())
    new_app = firebase_admin.initialize_app(cred,
                                            {'databaseURL': 'https://haucs-monitoring-default-rtdb.firebaseio.com'})
    new_ref = db.reference('/')
    return new_app, new_ref


def get_IP():
    terminalResponse = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    return terminalResponse.stdout


############### LOGGING ###############
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=folder + 'log.log', encoding='utf-8',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Starting with IP: ' + get_IP())

############### FIREBASE VARIABLES ###############
# Store Key in separate file !!!
cred = credentials.Certificate(folder + "fb_key.json")
app = firebase_admin.initialize_app(cred, {'databaseURL': 'https://haucs-monitoring-default-rtdb.firebaseio.com'})
ref = db.reference('/')

############### GLOBAL VARIABLES ###############
message_interval = 30 # seconds
last_message = time.time()

############### MAIN LOOP ###############
while True:

    if (time.time() - message_interval) >= last_message:
        last_message = time.time()
        off, on = collect_sample()
        data = {'off': off, 'on' : on}
        sensor_id = "egg_eye_1"
        message_time = time.strftime('%Y%m%d_%H:%M:%S', time.localtime(time.time()))
        try:
            sensor_ref = ref.child(sensor_id + "/data")
            sensor_ref.child(message_time).set(data)
        except:
            logger.warning("uploading data message failed")
            app, ref = restart_firebase(app)

############### END MAIN LOOP ###############

logger.warning("Exited While Loop")
ser.close()
