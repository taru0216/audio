#!/usr/bin/python

import glib
import gst
import gst.rtspserver
import logging
import os
import sys
import threading
import time
import urlparse

glib.threads_init()

logging.basicConfig(level=logging.DEBUG)

def init():
  os.system('jack_control start')

  plumbing = threading.Thread(target=_run_jack_plumbing)
  plumbing.setDaemon(True)
  plumbing.start()

def _run_jack_plumbing():
  # os.system('while true; do sleep 1; jack.plumbing -d demo/plumbing.conf; jack_lsp -c; done')
  os.system('jack.plumbing demo/plumbing.conf')

class AudioBackend(object):

  def __init__(self, name, model):
    super(AudioBackend, self).__init__()
    self.name = name
    self.model = model
    self._InitGlibLoop()
    self._InitGstreamer()
    self._InitBus()

    self.thread = threading.Thread(target=self._Worker)
    self.thread.setDaemon(True)

  def _InitGlibLoop(self):
    self.loop = glib.MainLoop()

  def _InitBus(self):
    if self.player:
      bus = self.player.get_bus()
      if bus:
        bus.add_signal_watch()
        bus.connect("message", self.OnMessage)

  def OnMessage(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_EOS:
      self.player.set_state(gst.STATE_NULL)
    elif t == gst.MESSAGE_ERROR:
      self.player.set_state(gst.STATE_NULL)
      err, debug = message.parse_error()
      logging.warn('%s: %s', err, debug)
    logging.debug(message)

  def Run(self):
    if not self.thread.isAlive():
      self.thread.start()

  def Play(self, path=None):
    self.Terminate()
    if path:
      logging.debug("Playing %s..." % path)
      self.player.set_property("uri", "file://" + path)
    self.player.set_state(gst.STATE_PLAYING)
    self.Run()

  def IsPlaying(self):
    return self.player.get_state()[1] == gst.STATE_PLAYING

  def _Worker(self):
    logging.debug('running glib loop %s', self.thread.getName())
    self.loop.run()
    logging.debug('glib loop finished %s', self.thread.getName())

  def Pause(self):
    self.player.set_state(gst.STATE_PAUSED)

  def Terminate(self):
    self.player.set_state(gst.STATE_NULL)

  def Wait(self):
    while self.thread.isAlive():
      self.thread.join(1)


CLIENT_NAME = 'makuhari'


class DemoReceiver(AudioBackend):

  def _InitGstreamer(self):
    self.player = gst.element_factory_make("playbin2", "player")
    fakesink = gst.element_factory_make("testsink", "sink")

    jacksink = gst.element_factory_make("jackaudiosink", "jacksink")
    jacksink.set_property("client-name",
                          "%s_%s" % (CLIENT_NAME, self.name))
    jacksink.set_property("connect", 0)

    self.player.set_property("video-sink", fakesink)
    # self.player.set_property("audio-sink", fakesink)
    self.player.set_property("audio-sink", jacksink)

  def OnMessage(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_EOS:
      path = urlparse.urlparse(self.player.get_property("uri"))[2]
      logging.debug('Replaying %s...' % path)
      self.Play(path)
    elif t == gst.MESSAGE_ERROR:
      self.player.set_state(gst.STATE_NULL)
      err, debug = message.parse_error()
      logging.warn('%s: %s', err, debug)
    logging.debug(message)


class StreamingReceiver(AudioBackend):

  def _InitGstreamer(self):
    self.player = gst.element_factory_make("fakesrc", "src")


class PhysicalSpeaker(AudioBackend):

  def _InitGstreamer(self):
    self.player = gst.Pipeline("player")
    jacksrc = gst.element_factory_make("jackaudiosrc", "jacksrc")
    jacksrc.set_property("client-name",
                         "%s_%s" % (CLIENT_NAME, self.name))
    jacksrc.set_property("connect", 0)
    audiosink = gst.element_factory_make("autoaudiosink", "audiosink")
    self.player.add(jacksrc, audiosink)
    gst.element_link_many(jacksrc, audiosink)


class RtspServerSpeaker(AudioBackend):

  Server = gst.rtspserver.Server()
  Mapping = Server.get_media_mapping()
  Loop = None

  Bitrates = [ 48000, 64000, 96000, 128000 ]


  ActiveFactories = {}

  @classmethod
  def _RunServer(cls):
    if not cls.Loop:
      cls.Loop = glib.MainLoop()
      if cls.Server.attach():
        t = threading.Thread(target=cls.Loop.run)
        t.setDaemon(True)
        t.start()

  def _InitGstreamer(self):
    self.player = None

  def IsPlaying(self):
    return self.__class__.ActiveFactories.has_key(self.endpoint)

  def _GenFactory(self, bitrate):
    launch = "jackaudiosrc client-name=%s_%s?bitrate=%s connect=0 name=jacksrc ! audioconvert ! ffenc_aac bitrate=%s ! queue ! rtpmp4apay name=pay0" % (CLIENT_NAME, self.name, bitrate, bitrate)

    factory = gst.rtspserver.MediaFactory()
    factory.set_shared(True)
    factory.set_launch(launch)

    return factory

  def _RegisterFactory(self, factory, bitrate, default=False):
      endpoint = self.endpoint
      if not default:
        endpoint = "%s/%s" % (self.endpoint, bitrate)
      self.__class__.Mapping.add_factory(endpoint, factory)
      self.factory_variants[endpoint] = factory

  def Play(self, path=None):

    self.endpoint = "/%s" % self.name
    self.factory_variants = {}

    default_bitrate = sorted(self.__class__.Bitrates)[-1]
    default_factory = None

    for bitrate in self.__class__.Bitrates:
      factory = self._GenFactory(bitrate)
      if bitrate == default_bitrate:
        default_factory = factory
      self._RegisterFactory(factory, bitrate)

    if default_factory:
      self._RegisterFactory(default_factory, default_bitrate, default=True)

    self.__class__.ActiveFactories[self.endpoint] = self.factory_variants

    self.model.bitrates = self.__class__.Bitrates

    self.__class__._RunServer()

  def Terminate(self):
    pass


def main(argv):
  threads = []
  for i in range(int(argv[1])):
    threads.append(AudioBackend())

  for thread in threads:
    thread.Play(argv[2])
    time.sleep(1)

#    for thread in threads:
#      thread.Pause()
#      time.sleep(3)

#    for thread in threads:
#      thread.Play()
#      time.sleep(3)

#  for thread in threads:
#    thread.Terminate()

  for thread in threads:
    thread.Wait()

init()

if __name__ == '__main__':
  main(sys.argv)
