#!/usr/bin/env python
import time
import random
import opc

ADDRESS = '10.42.0.42:7890'

client = opc.Client(ADDRESS)

while True:
    my_pixels = [(255, 0, 0), (0, 0, 0), (0, 0, 0)]
    random.shuffle(my_pixels)
    client.put_pixels(my_pixels, channel=0)
    time.sleep(1)

