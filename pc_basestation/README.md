# Setting up a new RPI Basestation

1. Clone this library into the desktop folder on the raspberry pi.

1. Install libraries using the command `pip3 install -r "rpi_list.txt"`.

1. Update the crontab to run the python script on reboot using the command `crontab -e` and adding the following line: "@reboot sleep 30 && /usr/bin/python3 ~/Desktop/Biomass/pc_basestation/gateway.py >> ~/Desktop/Bio>"

1. If you want to restart the raspberry pi daily copy the following line using `sudo crontab -e`: "0 */12 * * * /sbin/shutdown -r"
