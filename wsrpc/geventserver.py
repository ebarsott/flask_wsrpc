#!/usr/bin/env python

import inspect
import os

import flask
import flask_sockets
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from . import wrapper


module_directory = os.path.dirname(inspect.getfile(inspect.currentframe()))
static_directory = os.path.join(module_directory, 'static')
templates_directory = os.path.join(module_directory, 'templates')

server = flask.Flask(
    'rpc', static_folder=static_directory,
    template_folder=templates_directory)
sockets = flask_sockets.Sockets(server)


def register(obj, url=None):
    if url is None:
        url = '/ws'

    @sockets.route(url)
    def websocket(ws):
        handler = wrapper.JSONRPC(obj, ws)
        while not ws.closed:
            gevent.sleep(0.001)
            handler.update()


def serve(default_route=True):
    if default_route:
        @server.route('/')
        def default():
            return flask.render_template('index.html')
    wsgi_server = pywsgi.WSGIServer(
        ('', 5000), server, handler_class=WebSocketHandler)
    wsgi_server.serve_forever()
