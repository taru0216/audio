#!/usr/bin/python


import json
import urlparse


class JsonView(object):

  def Render(self, handler, controller, model):
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    d = self.__class__.ToJson(handler, controller, model)
    handler.wfile.write(json.dumps(d, indent=True))

  @classmethod
  def ToJson(cls, handler, controller, model):
    d = model.ToJson()
    d['url'] = handler.GetRoot() + controller.GetPath()
    return d

class AudioController(object):

  def Render(self, handler, controller, model):
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/html')
    handler.end_headers()

    html = '<html><body>'
    html += '<h1>%s</h1>' % model.name

    html += '<h2>Receivers</h2>'
    for name in sorted(model.receivers.keys()):
      receiver = model.receivers[name]
      html += '<h3><a href="%s">%s</a></h3>' % (receiver.transport, name)
      html += '<iframe height=54 src="%s"></iframe>' % receiver.transport

    html += '<h2>Speakers</h2>'
    for name in sorted(model.speakers.keys()):
      speaker = model.speakers[name]
      html += '<h3><a href="%s">%s</a></h3>' % (speaker.transport, name)
      html += '<iframe height=54 src="%s"></iframe>' % speaker.transport

    html += '</body></html>'
    handler.wfile.write(html)


class ReceiverController(object):

  def Render(self, handler, controller, model):
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/html')
    handler.end_headers()

    action, value = ('/%s/play' % controller.GetPath(), 'Play')
    if controller.audio_backend.IsPlaying():
      action, value = ('/%s/stop' % controller.GetPath(), 'Stop')

    html = '<html><body><form method=POST action="%s"><input value="%s" type=submit></form></body></html>' % (action, value)
    handler.wfile.write(html)


class SpeakerController(object):

  def Render(self, handler, controller, model):
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/html')
    handler.end_headers()

    action, value = ('/%s/on' % controller.GetPath(), 'On')
    if controller.audio_backend.IsPlaying():
      action, value = ('/%s/off' % controller.GetPath(), 'Off')

    html = '<html><body><form method=POST action="%s"><input value="%s" type=submit></form></body></html>' % (action, value)
    handler.wfile.write(html)
