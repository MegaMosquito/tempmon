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

 
import pygame
pygame.init()
import RPi.GPIO as GPIO
import sys
import json
import urllib2
import threading
import time
import datetime
from flask import Flask


# Is this the indoor one (the "master"), or the outdoor one (the "slave")?
MASTER = True
SLAVE_IP = '192.168.123.96' # The SLAVE_IP field is ignored when MASTER is False

# How long between cycle of the main loop
SAMPLE_INTERVAL_IN_SEC = 10

# How long without a temperature update from slave before "master" complains?
SLAVE_TIMEOUT_SECS = (5 * 60)

# Javascript page load timeout
RELOAD_TIMEOUT_SECs = (2 * 30)

# How many consecutive reload failures before complaining server "unreachable"
RELOAD_FAILURE_MAX = 3

# For the BMP180 sensor, use the Adafruit library
import Adafruit_BMP.BMP085 as BMP085 # Imports the BMP library

# Create a BMP085 object to poll the BMP180 for indoor temperature data
BMP180 = BMP085.BMP085()

# Create the Flask instance that provides the web page
webpage = Flask(__name__)

# Configure the screen (physical size is 320x240)
SCREENSIZE = (640, 480)
 
# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (192, 0, 192)

# Constants
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6006

from flask import Flask
from flask import send_file
webapp = Flask('tempmon')

# Globals
localTempC = -9999.0
inTempF1 = -9999.0
outTempF1 = 9999.0
last = time.time() # Last update time in seconds
updated = datetime.datetime.now() # Last update date and time

# This function is a separate thread to call extract() periodically
def get_temperatures():

  global localTempC
  global outTempF
  global updated
  global last

  while True:

    # Get the temperature from the BMP180 sensor directly attached
    localTempC = BMP180.read_temperature()
    localTempC -= 3 # BMP180 seems to be about 3 degrees C off!!
    localTempF = (32.0 + 9.0 * localTempC / 5.0)
    localTempC1 = int(localTempC * 10.0) / 10.0
    localTempF1 = int(localTempF * 10.0) / 10.0
    print ("<-- localTemp (%0.1fC, %0.1fF)" % (localTempC1, localTempF1))

    # If this is the master, get the temperature fromn the slave
    if MASTER:
      inTempF1 = localTempF1
      data = urllib2.urlopen('http://' + SLAVE_IP + ':' + str(FLASK_PORT) + '/temp')
      j = json.load(data)
      slaveTempC = j['temp-C']
      slaveTempF = (32.0 + 9.0 * slaveTempC / 5.0)
      slaveTempC1 = int(slaveTempC * 10.0) / 10.0
      slaveTempF1 = int(slaveTempF * 10.0) / 10.0
      print ("<-- slaveTemp (%0.1fC, %0.1fF)" % (slaveTempC1, slaveTempF1))
      outTempF1 = slaveTempF1
      # Note the time of this update
      last = time.time()
      updated = datetime.datetime.now()

    # Chill out for a while
    time.sleep(SAMPLE_INTERVAL_IN_SEC)

# Functions needed only on the "master":
if MASTER:

  # This function is a thread to operate the pygame loop for each frame
  def screen_handler():

    screen = pygame.display.set_mode(SCREENSIZE)
    pygame.display.set_caption("Temperature Monitor")
    pygame.mouse.set_visible(False)

    while True:

      # Handle keyboard and mouse events (not relevant for the headless RPi)
      done = False
      for event in pygame.event.get():  # User did something
        if event.type == pygame.QUIT:  # If user clicked close
          done = True  # Flag that we are done so we exit this loop
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
          done = True
      if done:
        pygame.quit()
        sys.exit(0)

      # Clear the screen and set the screen background
      screen.fill(BLACK)
 
      # Print text with selected font, size, bold, italics
      font = pygame.font.SysFont('Calibri', 300, True, False)
      smallfont = pygame.font.SysFont('Calibri', 45, True, False)

      # Set color based on relative temperature
      color = RED
      if (inTempF1 > outTempF1):
        color = GREEN

      # Outdoor temperature on top
      text = font.render(str(outTempF1) + "F", True, color)
      text = pygame.transform.rotate(text, 0)
      screen.blit(text, [SCREENSIZE[0] // 2 - text.get_width() // 2, 10])

      # Indoor temperature below that
      text = font.render(str(inTempF1) + "F", True, BLUE)
      text = pygame.transform.rotate(text, 0)
      screen.blit(text, [SCREENSIZE[0] // 2 - text.get_width() // 2, 230])

      # Show last update time at bottom in fine print
      update_str = updated.strftime('%a, %b %-d at %-I:%M%p')
      text = smallfont.render("(" + str(update_str) + ")", True, PURPLE)
      text = pygame.transform.rotate(text, 0)
      screen.blit(text, [SCREENSIZE[0] // 2 - text.get_width() // 2, 440])
 
      # Go ahead and update the screen with what we've drawn.
      # This MUST happen after all the other drawing commands.
      pygame.display.flip()
 
      # Pause the while loop for a while (in milliseconds) before repeating
      pygame.time.wait(100)

# This routine implements the web page
def tempmon(sideways):
  rot = '0'
  if '' != sideways:
    rot = 'Math.PI / 2'
  # Set color based on relative temperature
  color = 'red'
  if (inTempF1 > outTempF1):
    color = 'green'
  update_str = "* Last update: " + updated.strftime('%a, %b %-d at %-I:%M%p')
  elapsed = time.time() - last
  update_info = ''
  if elapsed > COMPLAIN_AFTER_SECS:
    update_info = '' + \
    '      ctx.font = "bolder 80px Arial";\n' + \
    '      ctx.fillStyle = "red";\n' + \
    '      ctx.fillText("' + update_str + '", canvas.width/2, canvas.height/2 + 700);\n' + \
    ''
  # '    <meta http-equiv="refresh" content="20">\n' + \
  return \
    '<!DOCTYPE html>\n' + \
    '<html>\n' + \
    '  <head>\n' + \
    '    <style>\n' + \
    '      body {\n' + \
    '        background-color: black;\n' + \
    '      }\n' + \
    '      #tempmon {\n' + \
    '        position: absolute;\n' + \
    '        width: 100%;\n' + \
    '        height: 100%;\n' + \
    '      }\n' + \
    '    </style>\n' + \
    '  </head>\n' + \
    '  <body">\n' + \
    '    <canvas id="tempmon", width=2000, height=2000></canvas>\n' + \
    '    <script>\n' + \
    '      var fails = 0;\n' + \
    '      var outTempF1 = ' + str(outTempF1) + ';\n' + \
    '      var inTempF1 = ' + str(inTempF1) + ';\n' + \
    '      var canvas = document.getElementById("tempmon");\n' + \
    '      var ctx = canvas.getContext("2d");\n' + \
    '      ctx.fillStyle = "black";\n' + \
    '      ctx.fillRect(0, 0, canvas.width, canvas.height);\n' + \
    '      ctx.translate(canvas.width / 2, canvas.height / 2);\n' + \
    '      ctx.rotate(' + rot + ');\n' + \
    '      ctx.translate(- canvas.width / 2, - canvas.height / 2);\n' + \
    '      ctx.font = "bolder 320px Arial";\n' + \
    '      ctx.textAlign = "center";\n' + \
    '      ctx.fillStyle = "' + color + '";\n' + \
    '      ctx.fillText("Out: " + (outTempF1.toFixed(1)) + "F", canvas.width/2, canvas.height/2 - 180);\n' + \
    '      ctx.fillStyle = "blue";\n' + \
    '      ctx.fillText(" In: " + (inTempF1.toFixed(1)) + "F", canvas.width/2, canvas.height/2 + 180);\n' + \
           update_info + \
    '    </script>\n' + \
    '  </body>\n' + \
    '</html>\n'

# Entry point for URL, "/temp"
@webpage.route('/temp')
def temp_route():
  return '{"temp-C":' + localTempC + '}\n'

# Entry point for URL, "/"
@webpage.route('/')
def straight_route():
  return tempmon('')

# Entry point for URL, "/..."
@webpage.route('/<sideways>')
def sideways_route(sideways):
  return tempmon('sideways')

if __name__ == '__main__':

  # Start the pygame thread (which handles the drawing on the TFT screen)
  s = threading.Thread(target=screen_handler, args=())
  s.start()

  # Start the temperature collection thread
  t = threading.Thread(target=get_temperatures, args=())
  t.start()

  # Fire up the webpage thread (turn off reloader and debug for pygame)
  webpage.debug = False
  webpage.use_reloader = False
  webpage.run(host='0.0.0.0', port=80)

#   '      setInterval(function() {\n' + \
#   '        try {\n' + \
#   '          fetch("./")\n' + \
#   '            .then(data => {\n' + \
#   '              window.location.reload();\n' + \
#   '            })\n' + \
#   '            .catch(err => {\n' + \
#   '              fails = fails + 1;\n' + \
#   '              console.log("Cannot load page!  fails=" + fails);\n' + \
#   '              if (fails > ' + str(RELOAD_FAILURE_MAX) + ') {\n' + \
#   '                ctx.font = "bolder 80px Arial";\n' + \
#   '                ctx.fillStyle = "red";\n' + \
#   '                ctx.fillText("* Server is unreachable!", canvas.width/2, canvas.height/2 + 600);\n' + \
#   '              }\n' + \
#   '            });\n' + \
#   '        }\n' + \
#   '        catch(err) {\n' + \
#   '          console.log("Failed to reload page.");\n' + \
#   '        }\n' + \
#   '      }\n' + \
