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

import sys
import json
import urllib2
import signal
import time
import datetime
import threading
import RPi.GPIO as GPIO

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (192, 0, 192)

# Basic disablable logging
DEBUG = False
def debug(s):
  if DEBUG: print(s)


# Create a screen update thread
class MyScreen(threading.Thread):

  # Configure the screen drawing size (physical size is 320x240)
  SCREENSIZE = (320, 240)

  # Pause betweens cycles of the pygame main loop (in milliseconds)
  PAUSE_BETWEEN_LOOPS_MSEC = 100

  def __init__(self):
    threading.Thread.__init__(self)
    self.screen = pygame.display.init()
    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN|pygame.NOFRAME, 0, 0)
    pygame.display.set_caption("Temperature Monitor")
    pygame.mouse.set_visible(False)
    self.inTempF = -9999.0
    self.outTempF = 9999.0
    self.done = False

  def set_inside(self, inTempF):
    self.inTempF = inTempF

  def set_outside(self, outTempF):
    self.outTempF = outTempF

  def stop(self):
    debug("Terminating screen update loop!")
    GPIO.cleanup()
    self.done = True

  def run(self):

    # Setup the backlight brightness (do this after initializing the screen)
    #GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    PWM_FREQUENCY = 2000
    backlight_percent = GPIO.PWM(18, PWM_FREQUENCY)
    backlight_percent.start(20)

    # PyGame looping forever
    while not self.done:

      debug("--> inTempF=%0.1fF, outTempF=%0.1fF" % (self.inTempF, self.outTempF))

      # Clear the screen and set the screen background
      self.screen.fill(BLACK)
 
      # Print text with selected font, size, bold, italics
      font = pygame.font.SysFont('Calibri', 100, True, False)
      smallfont = pygame.font.SysFont('Calibri', 20, True, False)

      # Set color based on relative temperature
      color = RED
      if (self.inTempF > self.outTempF):
        color = GREEN

      # Outdoor temperature on top
      text = font.render(("%0.1fF" % self.outTempF), True, color)
      text = pygame.transform.rotate(text, 0)
      self.screen.blit(text, [MyScreen.SCREENSIZE[0] // 2 - text.get_width() // 2, 45])

      # Indoor temperature below that
      text = font.render(("%0.1fF" % self.inTempF), True, BLUE)
      text = pygame.transform.rotate(text, 0)
      self.screen.blit(text, [MyScreen.SCREENSIZE[0] // 2 - text.get_width() // 2, 125])

      # Show last update time at bottom in a small font
      #update_str = updated.strftime('%a, %b %-d at %-I:%M%p')
      #text = smallfont.render("(" + str(update_str) + ")", True, PURPLE)
      #text = pygame.transform.rotate(text, 0)
      #self.screen.blit(text, [MyScreen.SCREENSIZE[0] // 2 - text.get_width() // 2, 220])
 
      # Go ahead and update the screen with what we've drawn.
      # This MUST happen after all the other drawing commands.
      pygame.display.flip()
 
      # Pause the while loop for a while (in milliseconds) before repeating
      pygame.time.wait(MyScreen.PAUSE_BETWEEN_LOOPS_MSEC)

    debug("Screen update loop terminated!")


# --- Test shell ---


# Global instance
my_screen = None

# Signal handler for clean exit
def signal_handler(sig, frame):
  debug('\n\n***** Received signal: {}'.format(sig))
  my_screen.stop()
  time.sleep(0.5)
  sys.exit(0)

# Test this thing
if __name__ == '__main__':

  # Create a new temp object with specified temp modifier, and polling rate
  my_screen = MyScreen()
  my_screen.start()

  # Install the signal handler
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # Loop forever
  n = 50
  while True:
    my_screen.set_inside(n)
    my_screen.set_outside(n)
    n+=5
    if n > 110: n = 50
    time.sleep(1)

if __name__ == '__main__':
  main()

