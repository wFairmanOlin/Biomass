import serial
import csv
import time
import os
from datetime import datetime

# THE GREAT PUMPKIN PLOTTER

def writeCSV(file, time, data):
    with open(file,'a',newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=',')
      writer.writerow([time, *data])

def init_serial(port):
    global ser

    ser = serial.Serial(port=port, baudrate=115200,
                         parity=serial.PARITY_NONE,
                          stopbits=serial.STOPBITS_ONE,
                           bytesize=serial.EIGHTBITS,
                            timeout=0)
    return ser


def init_file(header):
    filePath = "data"

    # date = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    date = str(input("name: "))
    global duration
    duration = int(input("sample len: "))

    if not os.path.exists(filePath):
        os.mkdir(filePath)

    csvFile = filePath + "/" + date + ".csv"

    with open(csvFile,'w',newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=',')
      writer.writerow(header)

    return csvFile

    
header = ['time', 'name', 'value']
port = '/dev/tty.usbmodem101'
ser  = init_serial(port)
file = init_file(header)

#send start phrase
ser.write('b'.encode('utf-8'))



time_start = time.time()
time_csv = time.time()
time_end = time_start + duration
buf = ''

while (time_end - time.time() > 0):
    
    c = ser.read()

    if c:
        char = str(c)
        char = char[-2]
        if char == 'r' or char == 'n':
            split = buf.find(',')
            if split == -1:
                continue
                # print(buf)
                # print("missed input")
            else:
                print(buf[split + 1 :])
                time_csv = time.time()
                writeCSV(file, time_csv - time_start, [buf[: split], buf[split + 1 :]])
            buf = ''
        else:
            buf += char

ser.write('s'.encode('utf-8'))
ser.close()