#!/usr/bin/env python

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
# $ sudo easy_install colormath
from colormath.color_objects import *


#-------------------------------------------------------------------------------
# command line

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
# parse layout file

print
print '    parsing layout file'
print


def computeRegion(cube, channel, ledindex):
    regionmap = {
        (0,0): [ (30, "off"), (60, "off"), (90, "C"), (999, "C") ],
        (0,1): [ (30, "BC"), (60, "B"), (90, "off"), (999, "off") ],
        (0,2): "A",
        (0,3): "off",
        (0,4): "AB",
        (0,5): "off",
        (0,6): "B",
        (0,7): "off",
        (1,0): [ (30, "off"), (60, "off"), (90, "A"), (999, "A") ],
        (1,1): [ (30, "AC"), (60, "C"), (90, "off"), (999, "off") ],
        (1,2): "B",
        (1,3): "off",
        (1,4): "BC",
        (1,5): "off",
        (1,6): "C",
        (1,7): "off",
        (2,0): [ (30, "off"), (60, "off"), (90, "B"), (999, "B") ],
        (2,1): [ (30, "AB"), (60, "A"), (90, "off"), (999, "off") ],
        (2,2): "C",
        (2,3): "off",
        (2,4): "AC",
        (2,5): "off",
        (2,6): "A",
        (2,7): "off",

    }
    r = regionmap[(cube, channel)]
    if not isinstance(r, list):
        return r
    else:
        for item in r:
            if ledindex < item[0]:
                return item[1]
    
    print "error: unmapped region"
    return "?"

coordinates = []
channels = []
regions = []

for item in json.load(open(options.layout)):

    if 'point' in item:
        coordinates.append(tuple(item['point']))
    if 'channel' in item:
        channels.append(item['channel'])
        if 'cube' in item and 'ledindex' in item:
            regions.append(computeRegion(item['cube'], item['channel'], item['ledindex']))

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
# color function

def pixel_color(t, coord, ii, n_pixels, random_values):
    """Compute the color of a given pixel.

    t: time in seconds since the program started.
    ii: which pixel this is, starting at 0
    coord: the (x, y, z) position of the pixel as a tuple
    n_pixels: the total number of pixels
    random_values: a list containing a constant random value for each pixel

    Returns an (r, g, b) tuple in the range 0-255

    """

    """
    # make moving stripes for x, y, and z
    x, y, z = coord
    y += color_utils.cos(x + 0.2*z, offset=0, period=1, minn=0, maxx=0.6)
    z += color_utils.cos(x, offset=0, period=1, minn=0, maxx=0.3)
    x += color_utils.cos(y + z, offset=0, period=1.5, minn=0, maxx=0.2)

    # rotate
    x, y, z = y, z, x

#     # shift some of the pixels to a new xyz location
#     if ii % 17 == 0:
#         x += ((ii*123)%5) / n_pixels * 32.12 + 0.1
#         y += ((ii*137)%5) / n_pixels * 22.23 + 0.1
#         z += ((ii*147)%7) / n_pixels * 44.34 + 0.1

    # make x, y, z -> r, g, b sine waves
    r = color_utils.cos(x, offset=t / 4, period=2.5, minn=0, maxx=1)
    g = color_utils.cos(y, offset=t / 4, period=2.5, minn=0, maxx=1)
    b = color_utils.cos(z, offset=t / 4, period=2.5, minn=0, maxx=1)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 1.4)

    clampdown = (r + g + b)/2
    clampdown = color_utils.remap(clampdown, 0.4, 0.5, 0, 1)
    clampdown = color_utils.clamp(clampdown, 0, 1)
    clampdown *= 0.9
    r *= clampdown
    g *= clampdown
    b *= clampdown

#     # shift the color of a few outliers
#     if random_values[ii] < 0.03:
#         r, g, b = b, g, r

    # black out regions
    r2 = color_utils.cos(x, offset=t / 10 + 12.345, period=4, minn=0, maxx=1)
    g2 = color_utils.cos(y, offset=t / 10 + 24.536, period=4, minn=0, maxx=1)
    b2 = color_utils.cos(z, offset=t / 10 + 34.675, period=4, minn=0, maxx=1)
    clampdown = (r2 + g2 + b2)/2
    clampdown = color_utils.remap(clampdown, 0.2, 0.3, 0, 1)
    clampdown = color_utils.clamp(clampdown, 0, 1)
    r *= clampdown
    g *= clampdown
    b *= clampdown

    # color scheme: fade towards blue-and-orange
#     g = (r+b) / 2
    g = g * 0.6 + ((r+b) / 2) * 0.4

#     # stretched vertical smears
#     v = color_utils.cos(ii / n_pixels, offset=t*0.1, period = 0.07, minn=0, maxx=1) ** 5 * 0.3
#     r += v
#     g += v
#     b += v

    # fade behind twinkle
    fade = color_utils.cos(t - ii/n_pixels, offset=0, period=7, minn=0, maxx=1) ** 20
    fade = 1 - fade*0.2
    r *= fade
    g *= fade
    b *= fade

    # twinkle occasional LEDs
    twinkle_speed = 0.07
    twinkle_density = 0.1
    twinkle = (random_values[ii]*7 + time.time()*twinkle_speed) % 1
    twinkle = abs(twinkle*2 - 1)
    twinkle = color_utils.remap(twinkle, 0, 1, -1/twinkle_density, 1.1)
    twinkle = color_utils.clamp(twinkle, -0.5, 1.1)
    twinkle **= 5
    twinkle *= color_utils.cos(t - ii/n_pixels, offset=0, period=7, minn=0, maxx=1) ** 20
    twinkle = color_utils.clamp(twinkle, -0.3, 1)
    r += twinkle
    g += twinkle
    b += twinkle

    # apply gamma curve
    # only do this on live leds, not in the simulator
    #r, g, b = color_utils.gamma((r, g, b), 2.2)
"""

def test_pixel_color(t, coord, ii, n_pixels, random_values):
    return ((ii % 30) / 30.0 * 125 + color_utils.cos(t) * 130, (1 - ii / n_pixels) * 180, color_utils.cos(t*0.1) * 255)

def quadrant(radians):
    radians = radians % math.pi * 2.0
    if 0 <= radians < math.pi / 2.0:
        return 1
    elif math.pi / 2.0 <= radians < math.pi:
        return 2
    elif math.pi <= radians < math.pi * 3.0/2.0:
        return 3
    elif math.pi * 3.0/2.0 <= radians:
        return 4
    else:
        return -1

def prism_color(t, coord, ii, n_pixels, random_values):
    arcwidth = math.pi/12.0
    theta = (t * math.pi/16.0) % (2.0 * math.pi)
    x, y, z, = coord
    #a = math.atan2(x, z) * 0.5 + math.pi
    #if a < 0:
    #    a = 2.0 * math.pi + a
    a = math.atan2(x, z) + math.pi

    #colors = ((255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 0, 128))

    #if quadrant(theta) == quadrant(a):
    #    return colors[quadrant(theta)-1]
    #else:
    #    return (240, 240, 240)

    delta = abs(theta - a)

    if delta > math.pi:
        delta = 2.0 * math.pi - delta

    if delta < arcwidth:
        p = delta / arcwidth
        c = HSLColor(360.0 * (1 - p), 1.0, 0.5)
        return c.convert_to('rgb').get_value_tuple()
    else:
        return (240, 240, 240)

def distance_color(t, coord, ii, n_pixels, random_values):
    x, y, z, = coord
    dist = math.sqrt(x * x + y * y + z * z)
    maxdist = 8.0
    c = HSLColor(360.0 * (t % 20)/20.0, 1.0, dist/maxdist)
    return c.convert_to('rgb').get_value_tuple()

def channel_color(t, coord, ii, n_pixels, random_value):
    c = HSLColor(320.0 / 8.0 * channels[ii], 0.8, 0.4)
    return c.convert_to('rgb').get_value_tuple()

def region_color(t, coord, ii, n_pixels, random_value):
    c = {
        'A': (0, 1.0, 0.5),
        'AB': (30, 1.0, 0.5),
        'B': (60, 1.0, 0.5),
        'BC': (90, 1.0, 0.5),
        'C': (120, 1.0, 0.5),
        'AC': (150, 1.0, 0.5),
        'off': (0, 0, 0),
    }.get(regions[ii], (0, 0.3, 0.6))

    return HSLColor(c[0], c[1], c[2]).convert_to('rgb').get_value_tuple()

#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print

n_pixels = len(coordinates)
random_values = [random.random() for ii in range(n_pixels)]
start_time = time.time()
while True:
    t = time.time() - start_time
    pixels = [region_color(t*0.6, coord, ii, n_pixels, random_values) for ii, coord in enumerate(coordinates)]
    client.put_pixels(pixels, channel=0)
    time.sleep(1 / options.fps)

