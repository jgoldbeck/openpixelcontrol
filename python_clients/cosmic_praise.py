#!/usr/bin/env python

# Cosmic Praise
# OpenPixelControl test program
# 7/18/2014

from __future__ import division
import time
import sys
import optparse
import random
import math
try:
    import json
except ImportError:
    import simplejson as json

import opc 
import color_utils

# remember to 
# $ sudo pip install colormath
from colormath.color_objects import *
from colormath.color_conversions import convert_color

# $ sudo pip install python-rtmidi --pre
import rtmidi
from rtmidi.midiutil import open_midiport
from rtmidi.midiconstants import *


#-------------------------------------------------------------------------------
# parse command line

parser = optparse.OptionParser()
parser.add_option('-l', '--layout', dest='layout',
                    action='store', type='string',
                    help='layout file')
parser.add_option('-s', '--server', dest='server', default='127.0.0.1:7890',
                    action='store', type='string',
                    help='ip and port of server')
parser.add_option('-f', '--fps', dest='fps', default=20,
                    action='store', type='int',
                    help='frames per second')

options, args = parser.parse_args()

if not options.layout:
    parser.print_help()
    print
    print 'ERROR: you must specify a layout file using --layout'
    print
    sys.exit(1)


#-------------------------------------------------------------------------------
# create MIDI event listener

events = []

class MidiInputHandler(object):
    def __init__(self, port):
        self.port = port
        self._wallclock = time.time()

    def __call__(self, event, data=None):
        event, deltatime = event
        self._wallclock += deltatime
        print "[%s] @%0.6f %r" % (self.port, self._wallclock, event)

        if event[0] < 0xF0:
            channel = (event[0] & 0xF) + 1
            status = event[0] & 0xF0
        else:
            status = event[0]
            channel = None

        data1 = data2 = None
        num_bytes = len(event)

        if num_bytes >= 2:
            data1 = event[1]
        if num_bytes >= 3:
            data2 = event[2]

        events.append( (channel, data1, data2, time.time()) )

try:
    midiin, port_name = open_midiport(None, use_virtual=True)
except (EOFError, KeyboardInterrupt):
    print "Error opening MIDI port"
    sys.exit()

print "Attaching MIDI input callback handler."
midiin.set_callback(MidiInputHandler(port_name))


#-------------------------------------------------------------------------------
# parse layout file

print
print '    parsing layout file'
print

coordinates = []

for item in json.load(open(options.layout)):
    if 'point' in item:
        coordinates.append(tuple(item['point']))
    

#-------------------------------------------------------------------------------
# connect to server

client = opc.Client(options.server)
if client.can_connect():
    print '    connected to %s' % options.server
else:
    # can't connect, but keep running in case the server appears later
    print '    WARNING: could not connect to %s' % options.server
print


#-------------------------------------------------------------------------------
# define color effects

def distance(x1, y1, x2, y2):
    v = (x2 - x1, y2 - y1)
    return math.sqrt(v[0] * v[0] + v[1] * v[1])

def plasma(t, accum, x, y):
    phase = accum
    stretch = 0.008 + (math.sin(t/20) ** 3 + 1.0) * 3.6
    p1 = ((math.sin(phase * 1.000) + 0.0) * 2.0, (math.sin(phase * 1.310) + 0.0) * 2.0)
    p2 = ((math.sin(phase * 1.770) + 0.0) * 2.0, (math.sin(phase * 2.865) + 0.0) * 2.0)
    d1 = distance(p1[0], p1[1], x, y)
    d2 = distance(p2[0], p2[1], x, y)
    f = (math.sin(d1 * d2 * stretch) + 1.0) * 0.5
    return f * f

def test_color(t, coord, ii, n_pixels, random_values, accum, trigger):
    c = None
    if trigger:
        c = HSLColor(330, 0.1, 0.6 + random.random() * 0.4)
    else:
        x, y, z, = coord
        theta = math.atan2(y, x)
        dist = math.sqrt(x * x + y * y + z * z)
        p = plasma(t, accum, theta, z)
        c = HSLColor(360.0 * (t % 6)/6.0 + 4 * dist - 30 * p, 0.6 + p/2, 0.5)
    return convert_color(c, sRGBColor).get_upscaled_value_tuple()


#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print

n_pixels = len(coordinates)
random_values = [random.random() for ii in range(n_pixels)]
start_time = time.time()
accum = 0
while True:
    frame_time = time.time()
    t = frame_time - start_time
    trigger = False
    if len(events) and events[-1][3] > (frame_time - 0.125):
        trigger = True
    pixels = [test_color(t*0.6, coord, ii, n_pixels, random_values, accum, trigger) for ii, coord in enumerate(coordinates)]
    accum = accum + 0.0001 * ( 1.0 + 80.0 * math.pow(math.sin(t/10), 3.0))
    client.put_pixels(pixels, channel=0)
    time.sleep(1 / options.fps)

