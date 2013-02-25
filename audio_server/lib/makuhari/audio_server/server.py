#!/sr/bin/python


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse

import controllers
import models
import sys


class AudioServerHandler(BaseHTTPRequestHandler):

  DefaultAudios = None
  AcceptFQDN = 'localhost'
  Controllers = {}

  @classmethod
  def InitControllers(cls):
    cls._AddController(controllers.HealthzController())
    cls._AddController(controllers.PdbzController())
    if cls.DefaultAudios:
      for audio in cls.DefaultAudios.itervalues():
        cls._AddAudio(audio)

  @classmethod
  def _AddController(cls, controller):
    cls.Controllers[controller.GetPath()] = controller

  @classmethod
  def _AddAudio(cls, audio):
    audio_controller = controllers.AudioController(audio)
    cls._AddController(audio_controller)
    for receiver in audio.receivers.itervalues():
      receiver_controller = controllers.ReceiverController(receiver,
                                                           audio_controller)
      cls._AddController(receiver_controller)
    for speaker in audio.speakers.itervalues():
      speaker_controller = controllers.SpeakerController(speaker,
                                                         audio_controller)
      cls._AddController(speaker_controller)

  def _LookupController(self):
    path = urlparse(self.path)[2]
    cls = self.__class__
    endpoints = sorted(cls.Controllers.keys(),
                       cmp=lambda x,y: cmp(len(y),len(x)))
    for endpoint in endpoints:
      endpoint_path = '/' + urlparse(endpoint)[2]
      if path.find(endpoint_path) == 0:
        return cls.Controllers[endpoint]
    return None

  def _DoMethod(self, controller, method):
    if controller:
      if not hasattr(controller, method):
        self.send_error(405)
        return
      else:
        return getattr(controller, method)(self)

    return self.ClientError()

  def do_GET(self):
    return self._DoMethod(self._LookupController(), 'do_GET')
 
  def do_POST(self):
    return self._DoMethod(self._LookupController(), 'do_POST')

  def do_PUT(self):
    return self._DoMethod(self._LookupController(), 'do_PUT')

  def do_DELETE(self):
    return self._DoMethod(self._LookupController(), 'do_DELETE')

  def GetRoot(self):
    return 'http://%s/' % self.__class__.AcceptFQDN
 
  def PutAudio(self):
    name = self.path.split('/')[2]
    audio = Audio(name, self.GenAudioURL(name))

    if name in self.audios:
      return self.ClientError(409, "audio '%s' already exists" % name)

    self._AddAudio(audio)
    self.send_response(201)
    self.send_header('Content-Type', 'application/json')
    self.end_headers()
    self.wfile.write(self.audios[name].ToJson())

  def ClientError(self, status=404, msg='Not found\n'):
    self.send_error(code=status, message=msg)


def main():
  try:
    server = HTTPServer(('',8888), AudioServerHandler)
    print 'server started'
    server.serve_forever()
  except KeyboardInterrupt:
    server.socket.close()
    print 'server stopped'


if __name__ == '__main__':
  AudioServerHandler.DefaultAudios = {}
  for audio in models.audios:
    AudioServerHandler.DefaultAudios[audio.name] = audio
  AudioServerHandler.AcceptFQDN = sys.argv[1]
  AudioServerHandler.InitControllers()

  main()
