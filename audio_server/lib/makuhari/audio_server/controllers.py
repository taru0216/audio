#!/usr/bin/python


import backend
import json
import logging
import models
import urlparse
import views


class Controller(object):

  def __init__(self, model=None, view=None):
    self.model = model
    self.views = {'html': view, 'json': views.JsonView()}

  def GetPath(self):
    return ""

  def do_GET(self, handler):
    qs = urlparse.parse_qs(urlparse.urlparse(handler.path)[4])

    view = self.views['html']
    if 'output' in qs:
      output = qs['output'][0]
      if output in self.views:
        view = self.views[output]

    if not view:
      view = self.views['json']

    view.Render(handler=handler,
                controller=self,
                model=self.model)

class AudioController(Controller):

  def __init__(self, model):
    super(AudioController, self).__init__(model, views.AudioController())

  def GetPath(self):
    return 'audio/%s/' % self.model.name

  def do_PUT(self, handler):
    name = handler.path.split('/')[2]
    audio = Audio(name, self.GenAudioURL(name))

    if name in self.audios:
      return self.ClientError(409, "audio '%s' already exists" % name)

    self._AddAudio(audio)
    self.send_response(201)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(self.audios[name].ToJson())


class ReceiverController(Controller):

  def __init__(self, model, audio_controller):
    super(ReceiverController, self).__init__(model, views.ReceiverController())
    self.audio_controller = audio_controller

    self.demo_path = None
    self.audio_backend = self._GenAudioBackend()

  def _GenAudioBackend(self):
    if self.model.type == 'streaming':
      return backend.StreamingReceiver(self.GetPath())
    elif self.model.type == 'demo':
      r = backend.DemoReceiver(self.GetPath())
      import os.path
      self.demo_path = os.path.abspath('demo/test_cbr.mp3')
      return r
    elif self.model.type == 'demo_Connect':
      r = backend.DemoReceiver(self.GetPath())
      import os.path
      self.demo_path = os.path.abspath('demo/Connect.mp3')
      return r

  def GetPath(self):
    return '%sreceiver/%s' % (self.audio_controller.GetPath(),
                              self.model.name)

  def do_POST(self, handler):
    path = urlparse.urlparse(handler.path)[2][1:]
    method = path[len(self.GetPath()):]

    if method == '/play':
      self.audio_backend.Play(self.demo_path)
    elif method == '/stop':
      self.audio_backend.Terminate()

    handler.send_response(303)
    handler.send_header('Location', '/%s' % self.GetPath())
    handler.end_headers()


class SpeakerController(Controller):

  def __init__(self, model, audio_controller):
    super(SpeakerController, self).__init__(model, views.SpeakerController())
    self.audio_controller = audio_controller

    self.audio_backend = self._GenAudioBackend()

  def _GenAudioBackend(self):
    if self.model.type == 'pysical':
      return backend.PhysicalSpeaker(self.GetPath())
    elif self.model.type == 'rtsp':
      b = backend.RtspServerSpeaker(self.GetPath())
      b.Play()
      return b

  def GetPath(self):
    return '%sspeaker/%s' % (self.audio_controller.GetPath(),
                             self.model.name)

  def do_POST(self, handler):
    path = urlparse.urlparse(handler.path)[2][1:]
    method = path[len(self.GetPath()):]

    if method == '/on':
      self.audio_backend.Play()
    elif method == '/off':
      self.audio_backend.Terminate()

    handler.send_response(303)
    handler.send_header('Location', '/%s' % self.GetPath())
    handler.end_headers()

class HealthzController(Controller):

  def GetPath(self):
    return 'healthz'

  def do_GET(self, handler):
    handler.send_response(200)
    handler.end_headers()
    handler.wfile.write("ok")


class PdbzController(Controller):

  def GetPath(self):
    return 'pdbz'

  def do_GET(self, handler):
    import pdb
    pdb.set_trace()
    handler.send_response(204)
    handler.end_headers()
