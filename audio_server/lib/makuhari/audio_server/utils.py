#!/usr/bin/python


import subprocess
import sys


def ParsePOSTData(fin):

  cmdline = 'gst-launch fdsrc fd=0 ! queue ! decodebin ! audioconvert ! audioresample ! jackaudiosink sync=false buffer-time=180000'
  p = subprocess.Popen(cmdline, shell=True, stdin=subprocess.PIPE)

  try:
    while True:
      chunk_length = int(fin.readline(), 16)
      if chunk_length == 0:
        break
      print >> sys.stderr, "Reading %d chunk bytes...." % chunk_length
      buf = fin.read(chunk_length)
      fin.readline()
      p.stdin.write(buf)
  finally:
    p.stdin.close()
    p.wait()
