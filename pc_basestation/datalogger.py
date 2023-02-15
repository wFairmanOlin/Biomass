import os
import csv
import serial
import time
import logging
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime


# Based off the THE GREAT PUMPKIN PLOTTER

######### COMPATIBLE SERIAL MESSAGES ##############


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


def writeCSV(file, time, data):
    with open(file,'a',newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=',')
      writer.writerow([time, *data])


def init_file(header):
    filePath = "data"

    date = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    if not os.path.exists(filePath):
        os.mkdir(filePath)

    csvFile = filePath + "/" + date + ".csv"

    with open(csvFile,'w',newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=',')
      writer.writerow(header)

    return csvFile

def processSensor(message):
    """
    Converts message list into a sensor data dictionary
    """
    data = dict()
    i = 1
    while i < len(message):
        data[i // 6 + 1] = {message[i] : message[i + 1], message[i + 2] : message[i + 3], 
                    message[i + 4] : message[i + 5]}
        i += 6

    return data

def uploadData(gdata, sdata, timestamp):
    """
    Uploads Data to the Real-Time Database in Firebase. Pond ID is currently
    hardcoded. Will be replaced by a lookup table in a future version
    """
    pid = str(findPond(gdata["LAT"], gdata["LNG"]))
    print(pid)

    #select pond
    pref = ref.child(pid)

    pref.child(timestamp).set({"GPSData" : gdata, "SensorData" : sdata})

############# LOGGING #################
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename='datalogger.log', encoding='utf-8', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.info('Starting')
############# SERIAL PORT VARIABLES ################
# port = '/dev/cu.usbserial-2'
# port = '/dev/cu.usbserial-0001'
port = '/dev/ttyACM0'
# port = '/dev/ttyUSB0'
ser  = init_serial(port)


############ FIREBASE VARIABLES ####################
#Store Key in separate file !!!
cred = credentials.Certificate("fb_key.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://haucs-monitoring-default-rtdb.firebaseio.com'})
ref = db.reference('/')


############ GLOBAL VARIABLES #####################
#serial input buffer
buf = b''

golay_timeout = 5
prev_id = -1
prev_time = 0
golay = dict()


########### MAIN LOOP ############################
while True:
    
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

            if len(message) >= 1:
                sensor_id = "bmass_" + str(int(message[1]) - 1)
                message_id = message[2]
                message_time = time.strftime('%Y%m%d_%H:%M:%S', time.localtime(time.time()))
                print(message_id + " " + message_time)
                
                if message_id == "status":
                    if len(message) == 11:
                        data = {message[3] : message[4], message[5] : message[6], message[7] : message[8], message[9] : message[10]}
                        try:
                            sensor_ref = ref.child(sensor_id + "/" + message_id)
                            sensor_ref.child(message_time).set(data)
                        except:
                            logger.exception("uploading status message failed")
                    else:
                        logger.warning("Status Message Length Mis-Match %s", message)

                if message_id == "golay_a":
                    prev_id = sensor_id
                    prev_time = time.time()
                    if len(message) == 35:
                        golay["seq_a"] = message[3:]
                    else:
                        logger.warning("Golay Message Length Mis-Match %s", message)
                
                if message_id == "golay_b":
                    if len(message) == 35:
                        if (prev_id == sensor_id) and ( (time.time() - prev_time) < golay_timeout):
                            golay["seq_b"] = message[3:]
                            try:
                                sensor_ref = ref.child(sensor_id + "/golay")
                                sensor_ref.child(message_time).set(golay)
                            except:
                                logger.exception("uploading golay message failed")
                        else:
                            logger.warning("Golay Timeout")
                    else:
                        logger.warning("Golay Message Length Mis-Match %s", message)
                    
    


ser.close()





