#!/usr/bin/python

# Expecting this hardware on the indoor ("master") temperature monitor::
#   https://www.adafruit.com/product/2315
# Based on the ILI9340:
#   https://cdn-shop.adafruit.com/datasheets/ILI9340.pdf
#
# *** HOST PREPARATION REQUIRED ***
#
# Follow the "installer script" instructions, here:
#   https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi/easy-install
# I.e., install their "adafruit-pitft.sh" script on the host, answering as follows:
#   Make these choices at the script prompts:
#     - PiTFT 2.2" no touch (240x320)
#     - 90 degrees (landscape)
#     - do *not* show console on PITFT
#     - do mirror PITFT on HDMI
#     - then allow the reboot
#   Or maybe this would work:
#     echo "2\n1\nn\ny\ny\n" | adafruit-pitft.sh
#

import os
import sys
import json
import urllib2
import signal
import time
import datetime
import threading


# Basic disablable logging
DEBUG = True
def debug(s):
  if DEBUG: print(s)


# Configuration from the environment
def get_from_env(v, d):
  if v in os.environ and '' != os.environ[v]:
    return os.environ[v]
  else:
    return d
MASTER = get_from_env('MASTER', '')
SLAVE_IP = get_from_env('SLAVE_IP', '')
DISPLAY = get_from_env('DISPLAY', ':0.0')


# Local modules
from temp import Temp
from web import MyServer
if 'yes' == MASTER:
  from screen import MyScreen


# Log setup info
print("\n\n\n")
print("****************************************")
print("****************************************")
print("****")
if 'yes' == MASTER:
  print("****   RUNNING AS MASTER!")
  print("****   Slave at: " + SLAVE_IP + ":80")
else:
  print("****   RUNNING AS SLAVE!")
print("****")
print("****************************************")
print("****************************************")
print("\n\n\n")


# Only setup pygame if this is the MASTER
if 'yes' == MASTER:
  import pygame
  pygame.init()


# Only setup for making web requests if this is the MASTER
if 'yes' == MASTER:
  import requests


# For the BMP180 sensor, use the Adafruit library
import Adafruit_BMP.BMP085 as BMP085 # Imports the BMP library

# Create a BMP085 object to poll the BMP180 for indoor temperature data
BMP180 = BMP085.BMP085()


# Constants
WEB_BIND_ADDRESS = '0.0.0.0'
WEB_BIND_PORT = 80
if 'yes' == MASTER:
  # Directory where the web server files will be served from
  SERVER_DIR = './www/'


# Globals
done = False
temp = None
web_server = None
if 'yes' == MASTER:
  my_screen = None


# Signal handler for clean exit
def signal_handler(sig, frame):
  debug('\n\n***** Received signal: {}'.format(sig))
  global done
  done = True
  temp.stop()
  web_server.stop()
  if 'yes' == MASTER:
    my_screen.stop()
  time.sleep(0.5)
  sys.exit(0)


# The main program, start thread, then update continuously
if __name__ == '__main__':

  # Install the signal handler
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # Create a new temp object with specified temp modifier, and polling rate
  temp = Temp(-3, 1)
  temp.start()

  # Create a new web server and bind it to the specified address:port
  web_server = MyServer(WEB_BIND_ADDRESS, WEB_BIND_PORT)
  web_server.start()

  # If this is the MASTER, setup slave URL, screen thread and web server thread
  if 'yes' == MASTER:

    # Construct the URL for getting the slave's temperature
    SLAVE_TEMP_URL = 'http://' + SLAVE_IP + ':' + str(WEB_BIND_PORT) + '/api/temp-F'
    debug("--> SLAVE_TEMP_URL = \"" + SLAVE_TEMP_URL + "\"")

    # Create a new screen handler object
    my_screen = MyScreen()
    my_screen.start()

    # And cache the filenames in the web server
    # NOTE: These files must be in the SERVER_DIR
    web_server.add_file("favicon.ico", 'image/x-icon')
    web_server.add_file("index.html", 'text/html')
    web_server.add_file("site.css", 'text/css')
    web_server.add_file("logo.png", 'image/png')


  # Loop forever 
  while not done:

    # Get the local temperature and update the REST server with it
    localTempF = temp.f()
    web_server.add_api("temp-F", localTempF)
    # If this is the MASTER, update it on the screen as well
    if 'yes' == MASTER:
      my_screen.set_inside(localTempF)

    # If this is the MASTER, then get remote temperature and deal with it
    if 'yes' == MASTER:
      try:
        # Try to get it fom the slave
        debug("--> URL=\"%s\"" % SLAVE_TEMP_URL)
        r = requests.get(SLAVE_TEMP_URL)
        if (r.status_code <= 299):
          # Got it. Decode, and tell REST server and screen about it
          j = r.json()
          # updated = datetime.datetime.now(),isoformat()
          updated = datetime.datetime.now().strftime('%a, %b %-d at %-I:%M%p')
          remoteTempF = j['temp-F']
          debug ("--> (local: %0.1fF, remote: %0.1fF, updated: %s)" % (localTempF, remoteTempF, updated))
          my_screen.set_outside(remoteTempF)
          my_screen.set_updated(updated)
          # Since this is the master, also put this in the REST server
          out = ('{"inside":%0.1f,"outside":%0.1f,"updated":"%s"}\n' % (localTempF, remoteTempF, updated))
          debug ('--> json:\n%s' % out)
          web_server.add_api("json", out)
        else:
          # Remote REST server gave an error code
          debug ("--> (local: %0.1fF, remote: *ERROR*)" % localTempF)
      except:
        # Remote REST server was unreachable
        debug ("--> (local: %0.1fF, remote: *UNREACHABLE*)" % localTempF)
    else:
      # Running as SLAVE, only local temperature is available
      debug ("--> (local: %0.1fF)" % localTempF)

    # Pause briefly
    time.sleep(5)


