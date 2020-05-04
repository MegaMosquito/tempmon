#!/usr/bin/python

import signal
import sys
import threading
import time

# For the BMP180 sensor, use the Adafruit library
import Adafruit_BMP.BMP085 # Imports the BMP library

# Basic disablable logging
DEBUG = False
def debug(s):
  if DEBUG: print(s)

# Create a Temp thread to poll the BMP180 for temperature data
class Temp(threading.Thread):

  SAMPLE_INTERVAL_SECS = 10

  # Temp constructor arguments:
  #  cMod:  number of Celsius degrees to add to the sensor (+/-)
  #  secs:  time between polls of the sensor (in seconds)
  def __init__(self, cMod, secs=SAMPLE_INTERVAL_SECS):
    threading.Thread.__init__(self)

    self.BMP180 = Adafruit_BMP.BMP085.BMP085()
    self.localTempC = -9999.0
    self.cMod = cMod
    self.secs = secs
    self.done = False

  @classmethod
  def C2F(cls, c):
    return (32.0 + 9.0 * c / 5.0)
  
  def c(self):
    return self.localTempC
 
  def f(self):
    return Temp.C2F(self.localTempC)
 
  def stop(self):
    debug("Terminating temperature collection loop!")
    self.done = True
 
  def run(self):

    while not self.done:

      # Get the temperature from the BMP180 sensor directly attached
      self.localTempC = self.BMP180.read_temperature() + self.cMod
      localTempC1 = int(self.localTempC * 10.0) / 10.0
      localTempF1 = int(Temp.C2F(self.localTempC) * 10.0) / 10.0
      debug ("<-- local temp is %0.1fC, %0.1fF." % (localTempC1, localTempF1))

      # Chill out for a while
      time.sleep(self.secs)

    debug("Temperature collection loop terminated!")


# --- Test shell ---


# Global instance
temp = None

# Signal handler for clean exit
def signal_handler(sig, frame):
  debug('\n\n***** Received signal: {}'.format(sig))
  temp.stop()
  time.sleep(0.5)
  sys.exit(0)

# Test this thing
if __name__ == '__main__':

  # Create a new temp object with specified temp modifier, and polling rate
  temp = Temp(-3, 1)
  temp.start()

  # Install the signal handler
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # Loop forever
  while True:
    debug ("--> (%0.1fC, %0.1fF)" % (temp.c(), temp.f()))
    time.sleep(3)

