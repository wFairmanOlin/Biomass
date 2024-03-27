import numpy as np
import firebase_admin
from firebase_admin import db
from firebase_admin import credentials
from scipy.fft import fft, fftfreq
import pickle
import subprocess
import time
import logging


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
folder = "Desktop/Biomass/egg_eye/code/"
# folder = "" #for testing


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
message_interval = 120 # seconds
last_message = time.time()

############### MAIN LOOP ###############
while True:
    
    try:
        #get the latest data
        adata = db.reference('/egg_eye_1/adcdata').order_by_key().limit_to_last(1).get()
        fdata = db.reference('/egg_eye_1/fdata').order_by_key().limit_to_last(2).get()
        data_key = list(adata.keys())[0]
        fs = adata[data_key]['fs']
        adata = np.array(adata[data_key]['data']).astype('float')
        fdata = np.array(fdata[data_key]['data']).astype('int')
        adata = adata/adata.max()
        fdata = fdata/fdata.max()
        
        #compute the FFT
        N = 512
        NDIV = 16
        a_fft = np.abs(fft(adata, N))[:N//2]
        f_fft = np.abs(fft(fdata, N))[:N//NDIV]

        #load algorithm
        with open(folder + 'lof_a_empty_trained.pickle', 'rb') as file:
            lofa = pickle.load(file)
        with open(folder + 'lof_f_empty_trained.pickle', 'rb') as file:
            loff = pickle.load(file)
        
        #upload if not already done
        last_predict = db.reference('/egg_eye_1/adetect').order_by_key().limit_to_last(1).get()

        if not last_predict:
            last_predict = '19990517' #some random old timestamp
        else:
            last_predict = list(last_predict.keys())[0]

        if last_predict != data_key:
            #calculate a data
            output = lofa.predict([a_fft])[0]
            output = 'outlier' if output == -1 else 'inlier'
            db.reference('/egg_eye_1/adetect').child(data_key).set(str(output))
            #calculate f data
            output = loff.predict([f_fft])[0]
            output = 'outlier' if output == -1 else 'inlier'
            db.reference('/egg_eye_1/fdetect').child(data_key).set(str(output))
    except:
        logger.warning("prediction failed")
        app, ref = restart_firebase(app)

    time.sleep(30)

############### END MAIN LOOP ###############

logger.warning("Exited While Loop")
ser.close()
