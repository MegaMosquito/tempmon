#!/usr/bin/python
import signal
import sys
import threading
import BaseHTTPServer

# Basic disablable logging
DEBUG = False
def debug(s):
  if DEBUG: print(s)

# Directory where the files will be served from
SERVER_DIR = './www/'

class MyServer(threading.Thread):

  class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    apis = dict()
    files = dict()

    def do_GET(self):
      debug('REST request: GET %s' % (self.path))
      # Enable typical `/` mapping to `/index.html`
      if '/' == self.path:
        p = ['', 'index.html']
      else:
        p = self.path.split('/')

      # Web server, dispensing files from SERVER_DIR
      if (len(p) == 2 and p[1] in MyServer.MyRequestHandler.files):
        # Web server request, with file in p[1]
        fn = p[1]
        t = MyServer.MyRequestHandler.files[fn]
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

      # REST API server, dispensing cached values from `/api/...` paths
      elif (len(p) == 3 and "api" == p[1] and p[2] in MyServer.MyRequestHandler.apis):
        # REST API request, with key in p[2]
        k = p[2]
        v = MyServer.MyRequestHandler.apis[k]
        debug('k=%s, v=%s' % (k, str(v)))
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if isinstance(v, str) :
          self.wfile.write('{"' + k + '":"' + v + '"}\n')
        else:
          self.wfile.write('{"' + k + '":' + str(v) + '}\n')
      else:
        self.send_error(404, ('Resource not found: %s' % self.path))

    @classmethod
    def add_api(cls, k, v):
      cls.apis[k] = v

    @classmethod
    def add_file(cls, fn, t):
      cls.files[fn] = t

  def __init__(self, bind_ip, bind_port):
    threading.Thread.__init__(self)
    self.done = False
    self.daemon = BaseHTTPServer.HTTPServer((bind_ip, bind_port), MyServer.MyRequestHandler)
    self.bind_ip = bind_ip
    self.bind_port = bind_port

  def add_api(self, k, v):
    MyServer.MyRequestHandler.add_api(k, v)

  def add_file(self, fn, t):
    MyServer.MyRequestHandler.add_file(fn, t)

  def run(self):
    debug("Web server is starting on %s:%s" % (self.bind_ip, self.bind_port))
    while not self.done:
      try:
        self.daemon.handle_request()
      except:
        pass
    self.daemon.server_close()
    debug("Web server daemon terminated!")

  def stop(self):
    debug("Terminating web server daemon!")
    self.done = True


# --- Test shell ---


import time

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
  server = MyServer('0.0.0.0', 80)
  server.start()

  # Cache some REST API data in the server
  server.add_api("temp-F", 999.9)

  # Cache some filenames in the server
  # NOTE: These files must be in the SERVER_DIR
  server.add_file("favicon.ico", 'image/x-icon')
  server.add_file("index.html", 'text/html')
  server.add_file("site.css", 'text/css')
  server.add_file("logo.png", 'image/png')

  # Loop forever poking the web server
  import subprocess
  COMMAND0 = 'curl -sS http://localhost:80/api/temp-F | jq .'
  COMMAND1 = 'curl -sS http://localhost:80/index.html'
  COMMAND2 = 'curl -sS http://localhost:80/'
  commands = [COMMAND0, COMMAND1, COMMAND2]
  i = 0
  while True:
    try:
      result = subprocess.check_output(['/bin/sh', '-c', commands[i]])
      output = result.decode('utf-8')
      debug(output)
      pass
    except:
      debug("Request failed.")
    i += 1
    if i >= len(commands):
      i = 0
    time.sleep(3)



