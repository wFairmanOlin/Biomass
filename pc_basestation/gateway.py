# Based off THE GREAT PUMPKIN PLOTTER
import os
import serial
import time
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime


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
# folder = "Desktop/Biomass/pc_basestation/"
folder = "" #for testing
#############################################


def init_serial(port):
    """
    Initialize Serial Port
    """
    global ser

    try: 
        ser = serial.Serial(port=port, baudrate=115200,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS,
                                timeout=0)
    except:
        logger.exception("serial init failed")
        raise

    return ser


############### LOGGING ###############
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=folder + 'log.log', encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)
logging.info('Starting')

############### SERIAL PORT VARIABLES ###############
# port = '/dev/cu.usbserial-2'
# port = '/dev/cu.usbserial-0001'
port = '/dev/ttyACM0'
# port = '/dev/ttyUSB0' #for RPI
ser  = init_serial(port)

############### FIREBASE VARIABLES ###############
#Store Key in separate file !!!
cred = credentials.Certificate(folder + "fb_key.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://haucs-monitoring-default-rtdb.firebaseio.com'})
ref = db.reference('/')

############### GLOBAL VARIABLES ###############
buf = b'' #serial input buffer

golay = dict()    #dictionary holding latest golay message
golay_timeout = 5 #max time (secs) to receive complete golay message
prev_id = -1      #id of last sensor to send a golay message
prev_time = 0     #time that previous golay message was received

last_message_received = time.time() #time that latest general message was received

############### MAIN LOOP ###############
while True:
    
    #Log Warning if No Message Received after 30 mins
    #reboot computer to power cycle the LoRa Receiver
    if (time.time() - last_message_received) > 1800:
        logger.warning("No Message Received for 30 Minutes")
        last_messaged_received = time.time()
        #os.system('sudo reboot')

    try:
        c = ser.read()
    except:
        logger.exception("reading serial buffer failed")

    if(c):
        buf = b''.join([buf, c])

        if buf[-1] == 13: #ends with carriage return
            message = buf.decode()
            message = message.split()
            buf = b''
            last_message_received = time.time()

            if len(message) >= 1:
                try:
                    sensor_id = "bmass_" + str(int(message[1]) - 1)
                except:
                    logger.warning("Invalid Sensor ID Received. Skipping ...")
                    continue

                message_id = message[2]
                message_time = time.strftime('%Y%m%d_%H:%M:%S', time.localtime(time.time()))
                # print(message_id + " " + message_time)
                
                if message_id == "status":
                    if len(message) == 9:
                        data = {message[3] : message[4], message[5] : message[6], message[7] : message[8]}
                        try:
                            sensor_ref = ref.child(sensor_id + "/" + message_id)
                            sensor_ref.child(message_time).set(data)
                        except:
                            logger.exception("uploading status message failed")
                    else:
                        logger.warning("Status Message Length Mis-Match %s", message)

                if message_id == "data":
                    if len(message) == 6:
                        try:
                            sensor_ref = ref.child(sensor_id + "/data")
                            sensor_ref.child(message_time).set(message[3:])
                        except:
                            logger.exception("uploading data message failed")
                    else:
                        logger.warning("Data Message Length Mis-Match %s", message)

                if message_id == "lat":
                    if len(message) == 8:
                        data = {message[2] : message[3], message[4] : message[5], message[6] : message[7]}
                        try:
                            sensor_ref = ref.child("gps")
                            sensor_ref.child(message_time).set(data)
                        except:
                            logger.exception("uploading gps message failed")
                    else:
                        logger.warning("GPS Message Length Mis-Match %s", message)
    
                # if message_id == "golay_a":
                #     prev_id = sensor_id
                #     prev_time = time.time()
                #     if len(message) == 35:
                #         golay["seq_a"] = message[3:]
                #     else:
                #         logger.warning("Golay Message Length Mis-Match %s", message)
                
                # if message_id == "golay_b":
                #     if len(message) == 35:
                #         if (prev_id == sensor_id) and ( (time.time() - prev_time) < golay_timeout):
                #             golay["seq_b"] = message[3:]
                #             try:
                #                 sensor_ref = ref.child(sensor_id + "/golay")
                #                 sensor_ref.child(message_time).set(golay)
                #             except:
                #                 logger.exception("uploading golay message failed")
                #         else:
                #             logger.warning("Golay Timeout or Interrupted by Another Sensor")
                #     else:
                #         logger.warning("Golay Message Length Mis-Match %s", message)
############### END MAIN LOOP ###############

logger.warning("Exited While Loop")
ser.close()

