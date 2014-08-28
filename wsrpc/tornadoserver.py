#!/usr/bin/env python

import inspect
import logging
import os

import flask
#import flask_sockets
import tornado
import tornado.web
import tornado.websocket
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop
import tornado.wsgi

from . import wrapper


logger = logging.getLogger(__name__)

module_directory = os.path.dirname(inspect.getfile(inspect.currentframe()))
static_directory = os.path.join(module_directory, 'static')
templates_directory = os.path.join(module_directory, 'templates')

server = flask.Flask(
    'rpc', static_folder=static_directory,
    template_folder=templates_directory)
#sockets = flask_sockets.Sockets(server)

obj_dict = {}


class ObjectHandler(WebSocketHandler):
    def initialize(self, obj=None, **kwargs):
        logger.debug("Initialized {}".format(obj))
        self.obj = obj
        # needs receive and send
        self.handler = wrapper.JSONRPC(obj, self, **kwargs)
        self.message = None
        logger.debug("done initialize")

    def receive(self):
        logger.debug("receive")
        return self.message

    def open(self):
        logger.debug("Web socket opened")

    def on_close(self):
        logger.debug("Web socket closed")

    def on_message(self, message):
        logger.debug("Received message {}".format(message))
        self.message = message
        self.handler.update()
        self.message = None

    def send(self, message):
        logger.debug("Sending message {}".format(message))
        self.write_message(message)


def register(obj, url=None, **kwargs):
    if url is None:
        url = 'ws'
    if kwargs is None:
        kwargs = {}
    kwargs['obj'] = obj
    obj_dict[url] = kwargs


def serve(default_route=True):
    if default_route:
        @server.route('/')
        def default():
            return flask.render_template('index.html')
    wsgi_app = tornado.wsgi.WSGIContainer(server)
    items = []
    for k in obj_dict:
        items.append(('/{}'.format(k), ObjectHandler, obj_dict[k]))
    items += [('.*', tornado.web.FallbackHandler, {'fallback': wsgi_app}), ]
    logger.debug("Serving items: {}".format(items))
    application = tornado.web.Application(items)
    application.listen(5000)
    loop = IOLoop.instance()
    if not loop._running:
        loop.start()
