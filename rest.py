#!/usr/bin/python

import signal
import sys
import threading
import time
import BaseHTTPServer

# Basic disablable logging
DEBUG = False
def debug(s):
  if DEBUG: print(s)

class RestServer(threading.Thread):

  class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    content = dict()

    def do_GET(req):
      debug('REST request: GET %s' % (req.path))
      p = req.path.split('/')
      if (len(p) <= 1) or not (p[1] in RestServer.MyRequestHandler.content):
        req.send_response(400)
      else:
        k = p[1]
        v = RestServer.MyRequestHandler.content[k]
        debug('k=%s, v=%s' % (k, str(v)))
        req.send_response(200)
        req.send_header('Content-type', 'application/json')
        req.end_headers()
        if isinstance(v, str) :
          req.wfile.write('{"' + k + '":"' + v + '"}\n')
        else:
          req.wfile.write('{"' + k + '":' + str(v) + '}\n')

    @classmethod
    def add(cls, k, v):
      cls.content[k] = v

  def __init__(self, bind_ip, bind_port):
    threading.Thread.__init__(self)
    self.done = False
    self.daemon = BaseHTTPServer.HTTPServer((bind_ip, bind_port), RestServer.MyRequestHandler)
    self.bind_ip = bind_ip
    self.bind_port = bind_port

  def add(self, k, v):
    RestServer.MyRequestHandler.add(k, v)

  def run(self):
    debug("REST server is starting on %s:%s" % (self.bind_ip, self.bind_port))
    while not self.done:
      #try:
        self.daemon.handle_request()
      #except:
      #  pass
    self.daemon.server_close()
    debug("REST server daemon terminated!")

  def stop(self):
    debug("Terminating REST server daemon!")
    self.done = True


# --- Test shell ---


# Global instance
server = None

# Signal handler for clean exit
def signal_handler(sig, frame):
  debug('\n\n***** Received signal: {}'.format(sig))
  server.stop()
  time.sleep(0.5)
  sys.exit(0)

# Test this thing
if __name__ == '__main__':

  import subprocess

  # Create a new server instance with specified bind address:port
  server = RestServer('0.0.0.0', 80)
  server.start()

  # Install the signal handler
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # Cache some data in the REST server
  server.add("temp-C", 12.34)

  # Loop forever poking the REST API
  COMMAND = 'curl -sS http://localhost:80/temp-C | jq .'
  while True:
    result = subprocess.check_output(['/bin/sh', '-c', COMMAND])
    output = result.decode('utf-8')
    debug(output)
    time.sleep(3)



