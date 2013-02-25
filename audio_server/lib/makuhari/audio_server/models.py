#!/usr/bin/python


import json


class Model(object):

  def __init__(self, name, description):
    self.name = name
    self.description = description

  def ToJson(self):
    return {'id': self.name, 'description': self.description}


class Device(Model):

  def __init__(self, name, description, type, transport = None):
    super(Device, self).__init__(name, description)
    self.type = type
    self.transport = transport

  def ToJson(self):
    d = super(Device, self).ToJson()
    d['type'] = self.type
    if self.transport:
      d['transport'] = self.transport
    return d


class Audio(Model):

  CONTENT_TYPE = 'application/json+wave+audio'
  VERSION = 'dev'

  def __init__(self, name, description):
    super(Audio, self).__init__(name, description)
    self.receivers = {}
    self.speakers = {}

  def AddReceiver(self, receiver):
    self.receivers[receiver.name] = receiver

  def GetReceiver(self, name):
    return self.receivers[name]

  def RemoveReceiver(self, name):
    return self.receivers.pop(name)

  def AddSpeaker(self, speaker):
    self.speakers[speaker.name] = speaker

  def GetSpeaker(self, name):
    return self.speakers[name]

  def RemoveSpeaker(self, name):
    return self.speakers.pop(name)

  def ToJson(self):
    d = super(Audio, self).ToJson()
    d['content-type'] = self.__class__.CONTENT_TYPE
    d['version'] = self.__class__.VERSION

    d['receivers'] = {}
    for name, receiver in self.receivers.iteritems():
      d['receivers'][name] = receiver.ToJson()
      
    d['speakers'] = {}
    for name, speaker in self.speakers.iteritems():
      d['speakers'][name] = speaker.ToJson()

    return d

  class Receiver(Device):
    pass

  class Speaker(Device):
    pass


# test
audios = []
for i in range(2):
  audio = Audio('demo%d' % i, 'Demo Audio %d' % i)
  line = Audio.Receiver(name='line0',
                        description='Streaming Demo Line Input',
                        type='streaming',
                        transport='/audio/demo%d/receiver/line0' % i)
  audio.AddReceiver(line)
  demo = Audio.Receiver(name='demo_player0',
                        description='Streaming Demo Player',
                        type='demo',
                        transport='/audio/demo%d/receiver/demo_player0' % i)
  audio.AddReceiver(demo)
  demo = Audio.Receiver(name='demo_Connect0',
                        description='Streaming Demo Player with Connect',
                        type='demo_Connect',
                        transport='/audio/demo%d/receiver/demo_Connect0' % i)
  audio.AddReceiver(demo)

  speaker0 = Audio.Speaker(name='speaker0',
                           description='Demo Pysical Output',
                           type='pysical',
                           transport='/audio/demo%d/speaker/speaker0' % i)
  audio.AddSpeaker(speaker0)

  rtsp0 = Audio.Speaker(name='rtsp0',
                        description='RTSP Output',
                        type='rtsp',
                        transport='/audio/demo%d/speaker/rtsp0' % i)
  audio.AddSpeaker(rtsp0)
  audios.append(audio)
