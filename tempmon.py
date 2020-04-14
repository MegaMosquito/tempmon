#!/usr/bin/python2

# Uses this hardware:
#   https://www.adafruit.com/product/2315
# And follow the "installer script" instructions, here:
#   https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi/easy-install
# Run their "adafruit-pitft.sh" script, answering as follows:
#   Make these choices at the script prompts:
#     - PiTFT 2.2" no touch (240x320)
#     - 270 degrees (landscape)
#     - do *not* show console on PITFT
#     - do mirror PITFT on HDMI

 
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


# These values need to be provided from the host
MY_OPENWEATHERMAP_APP_ID = os.environ['MY_OPENWEATHERMAP_APP_ID']


# How many seconds must elapse without a temperature update before complaining?
COMPLAIN_AFTER_SECS = (5 * 60)

# When to reload the data from the server
RELOAD_INTERVAL_SECS = 20

# How many reload failures before complaining
RELOAD_FAILURE_MAX = 3

# For the BMP180 sensor, use the Adafruit library
import Adafruit_BMP.BMP085 as BMP085 # Imports the BMP library

# Get your "APPID" at https://home.openweathermap.org/ (they email it to you)
OPENWEATHERAPI = 'http://api.openweathermap.org/data/2.5/weather?APPID=4a9bd3166311f9bb805b9a1fedb6f230&lat=37.273246&lon=-121.881315'

# Create a BMP085 object to poll the BMP180 for indoor temperature data
BMP180 = BMP085.BMP085()

# Create the Flask instance that provides the web page
webpage = Flask(__name__)

# Configure access to the data source in my weather station
URL = "http://192.168.123.98/livedata.htm"
SAMPLE_INTERVAL_IN_SEC = 60

# Configure for Twillio
user = "darlings.applicances@gmail.com"
pw = "IhOdHCVzj6Z1a4na0VJ26VajFMswsK8lCEOJjKOJ"

# Configure the screen (physical size is 320x240)
SCREENSIZE = (640, 480)
 
# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (192, 0, 192)

# Configure GPIO #17, #22, #23, #27, for the 4 buttons
BUTTON0 = 17
BUTTON1 = 22
BUTTON2 = 23
BUTTON3 = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON3, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# External probing target
EXTERNAL_PROBE_TARGET = 'https://www.google.com/'

# Constants
FLASK_BIND_ADDRESS = '0.0.0.0'
FLASK_PORT = 6006

  from flask import Flask
  from flask import send_file
  webapp = Flask('tempmon')



# Globals
inTemp = -9999.0
outTemp = 9999.0
last = time.time() # Last update time in seconds
updated = datetime.datetime.now() # Last update date and time

# This function is a separate thread to call extract() periodically
def get_temperatures():

  global inTemp
  global outTemp
  global updated
  global last

  while True:

    # Get the indoor temperature from the BMP180 sensor directly attached
    inTempC = BMP180.read_temperature()
    inTempX = (32.0 + 9.0 * inTempC / 5.0)
    inTemp = int(inTempX * 10.0) / 10.0
    inTemp -= 5 # My BMP180 is always pretty much exactly 5 degrees off!!
    #print ("<-- inTemp (", inTemp, ")")

    # Get data from the openweathermap.org REST API
    data = urllib2.urlopen(OPENWEATHERAPI)
    j = json.load(data)
    outTempK = j['main']['temp']
    outTempX = (32.0 + 9.0 * (outTempK - 273.15) / 5.0)
    outTemp = int(outTempX * 10.0) / 10.0
    #print ("<-- outTemp (", outTemp, ")")
    # Note the time of this update
    last = time.time()
    updated = datetime.datetime.now()

    # Chill out for a while so as not to pound the weatherstation API too hard
    time.sleep(SAMPLE_INTERVAL_IN_SEC)

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

    # Check the GPIO buttons:
    button0 = GPIO.input(BUTTON0) == GPIO.LOW
    button1 = GPIO.input(BUTTON1) == GPIO.LOW
    button2 = GPIO.input(BUTTON2) == GPIO.LOW
    button3 = GPIO.input(BUTTON3) == GPIO.LOW
    #print("B0:", button0, "- B1:", button1, "- B2:", button2, "- B3:", button3)

    # Clear the screen and set the screen background
    screen.fill(BLACK)
 
    # Print text with selected font, size, bold, italics
    font = pygame.font.SysFont('Calibri', 300, True, False)
    smallfont = pygame.font.SysFont('Calibri', 45, True, False)

    # Set color based on relative temperature
    color = RED
    if (inTemp > outTemp):
      color = GREEN

    # Outdoor temperature on top
    text = font.render(str(outTemp) + "F", True, color)
    text = pygame.transform.rotate(text, 0)
    screen.blit(text, [SCREENSIZE[0] // 2 - text.get_width() // 2, 10])

    # Indoor temperature below that
    text = font.render(str(inTemp) + "F", True, BLUE)
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
  if (inTemp > outTemp):
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
    '      var outTemp = ' + str(outTemp) + ';\n' + \
    '      var inTemp = ' + str(inTemp) + ';\n' + \
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
    '      ctx.fillText("Out: " + (outTemp.toFixed(1)) + "F", canvas.width/2, canvas.height/2 - 180);\n' + \
    '      ctx.fillStyle = "blue";\n' + \
    '      ctx.fillText(" In: " + (inTemp.toFixed(1)) + "F", canvas.width/2, canvas.height/2 + 180);\n' + \
           update_info + \
    '    </script>\n' + \
    '  </body>\n' + \
    '</html>\n'

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
