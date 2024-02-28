from smbus2 import SMBus
from MCP342x import MCP342x
import time

with SMBus(1) as bus:
    adc = MCP342x(bus, 0x68, channel=0, resolution=12)
    adc.set_scale_factor(2.482) # calibrated with a multimeter

    start = time.time()
    x = []
    for i in range(1000):
        x += [adc.convert_and_read()]
    end = time.time()
    print("time: ", end - start)