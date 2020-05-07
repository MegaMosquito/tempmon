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

# Directory where the files will be served from
SERVER_DIR = './www/'

class WebServer(threading.Thread):

  class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    content = dict()

    def do_GET(self):
      debug('REST request: GET %s' % (self.path))
      if '/' == self.path:
        p = ['', 'index.html']
      else:
        p = self.path.split('/')
      if (len(p) != 2) or not (p[1] in WebServer.MyRequestHandler.content):
        self.send_error(404, ('File Not Found: %s' % self.path))
      else:
        fn = p[1]
        t = WebServer.MyRequestHandler.content[fn]
        debug('fn=%s, t=%s' % (fn, t))
        try:
          f = open(SERVER_DIR + fn, 'rb')
          self.send_response(200)
          self.send_header('Content-type', t)
          self.end_headers()
          if t.startswith('text'):
            self.wfile.write(f.read().encode('utf-8'))
          else:
            self.wfile.write(f.read())
          f.close()
          return
        except IOError:
          self.send_error(404,'File Not Found: "%s"' % self.path)

    @classmethod
    def add(cls, fn, t):
      cls.content[fn] = t

  def __init__(self, bind_ip, bind_port):
    threading.Thread.__init__(self)
    self.done = False
    self.daemon = BaseHTTPServer.HTTPServer((bind_ip, bind_port), WebServer.MyRequestHandler)
    self.bind_ip = bind_ip
    self.bind_port = bind_port

  def add(self, fn, t):
    WebServer.MyRequestHandler.add(fn, t)

  def run(self):
    debug("Web server is starting on %s:%s" % (self.bind_ip, self.bind_port))
    while not self.done:
      #try:
        self.daemon.handle_request()
      #except:
      #  pass
    self.daemon.server_close()
    debug("Web server daemon terminated!")

  def stop(self):
    debug("Terminating web server daemon!")
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

  # Install the signal handler
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # Create a new server instance with specified bind address:port
  server = WebServer('0.0.0.0', 80)
  server.start()

  # Cache the filenames in the web server
  # NOTE: These files must be in the SERVER_DIR
  server.add("favicon.ico", 'image/x-icon')
  server.add("index.html", 'text/html')
  server.add("site.css", 'text/css')
  server.add("logo.png", 'image/png')

  # Loop forever poking the web server
  import subprocess
  #COMMAND = 'curl -sS http://localhost:80/index.html'
  COMMAND = 'curl -sS http://localhost:80/'
  while True:
    try:
      result = subprocess.check_output(['/bin/sh', '-c', COMMAND])
      output = result.decode('utf-8')
      debug(output)
      pass
    except:
      debug("Request failed.")
    time.sleep(3)



