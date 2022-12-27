#!/usr/bin/env python
#pylint: indent-string='  '

# Note:
# pip install pyserial
# pip install python-daemon
# pip install lockfile

import serial
import daemon
import signal
import lockfile
import time
import getopt
import os
import copy
import sys
import select
from threading import Event
from datetime import datetime
from subprocess import Popen

# Default options
PIDFILE = 'ivt490.pid'
SEROPTS = {
  "port": "/dev/ttyUSB0",
  "baudrate": 9600,
  "timeout": 5
  }
LOGFILE = "ivt490.log"
DONE_WAIT = 7

class App(object):
  def __init__(self, logfile, outputfile, port, foreground):
    self.logfile = os.path.abspath(logfile)
    self.outputfile = os.path.abspath(outputfile)
    self.port = port
    self.ser = None
    self.running = True
    self.foreground = foreground

  def log(self, msg):
    text = "%s: %s\n" % (str(datetime.now()), msg)
    with open(self.logfile, 'a') as f:
      f.write(text)
    if self.foreground:
      sys.stdout.write(text)

  def log_init(self):
    self.log("*** IVT490 readings daemon starting with options:")
    self.log("Log file = " + self.logfile)
    self.log("Output file = " + self.outputfile)
    self.log("Serial port = " + self.port)

  def publish(self, line):
    secs = time.time()
    csv = ";".join([field.strip() for field in line.split(";")])
    line = "%s;%s" % (secs, csv)
    if self.outputfile == "-":
      sys.stdout.write(line + "\n")
    else:
      ofile = time.strftime(self.outputfile, time.localtime())
      with open(ofile, "a") as fd:
        fd.write(line + "\n")

  def open_serial(self):
    try:
      opts = copy.copy(SEROPTS)
      opts["port"] = self.port
      self.log("Opening " + self.port + "...")
      self.ser = serial.Serial(**opts)
    except Exception as e:
      self.log("ERROR opening serial port: " + str(e))

  def safe_exit(self, *args):
    self.log("Caught TERM signal, exiting...")
    self.running = False

  def listen(self):
    self.log("Entering listen loop.")
    try:
      while self.running and self.ser:
        line = self.ser.readline()
        line = line.decode("ascii")
        if len(line) > 0 and line[0] != "\x00":
          self.publish(line.rstrip())
    except KeyboardInterrupt:
      self.log("Interrupted by user!")
    except:
      self.log("ERROR reading from serial port: " + str(sys.exc_info()[1]))

    if self.ser:
      try:
        self.ser.close()
      except:
        pass # ignore
    self.log("Listen loop ended.")


def usage():
  print(sys.argv[0] + ' [-h][-f] [-l log file] [-p pid_file] [-o receiver script] [-s serial port]')
  print('\t-l  : path to file that will receive log messages (default %s)' % (LOGFILE, ))
  print('\t-p  : path to file that will receive the daemon PID (default %s)' % (PIDFILE, ))
  print('\t-o  : path to file to which readings will be appended - will be run through strftime')
  print('\t-s  : serial port to get readings from (at %d baud, default %s)' % (SEROPTS["baudrate"], SEROPTS["port"], ))
  print("\t-f  : don't detach (run in foreground)")
  print('\t-h  : display this help')


def start():
  opts, args = getopt.getopt(sys.argv[1:], 'o:p:l:hfs:')
  pidfile = PIDFILE
  logfile = LOGFILE
  outputfile = None
  serport = SEROPTS["port"]
  foreground = False
  for o, a in opts:
    if o == '-o':
      outputfile = a
    elif o == '-p':
      pidfile = a
    elif o == '-l':
      logfile = a
    elif o == '-s':
      serport = a
    elif o == '-f':
      foreground = True
    elif o == '-h':
      usage()
      sys.exit(1)
  if not outputfile:
    print("Missing output file.")
    usage()
    sys.exit(2)

  a = App(logfile=logfile, outputfile=outputfile, port=serport, foreground=foreground)
  a.log_init()

  if foreground:
    a.log("Foreground mode")
    a.open_serial()
    a.listen()
  else:
    fullpid = os.path.abspath(pidfile)
    a.log("Daemon mode, setting up context.")
    a.log("PID file is %s" % (fullpid, )) 
    context = daemon.DaemonContext()
    context.umask = 0o002
    context.pidfile = lockfile.FileLock(fullpid)
    context.signal_map = {
      signal.SIGTERM: a.safe_exit
      }
    with context:
      a.log("Successfully daemonized!")
      a.open_serial()
      a.listen()

if __name__ == "__main__":
  start()
