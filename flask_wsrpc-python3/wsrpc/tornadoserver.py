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


def debug():
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

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
        print("OH: initialize")
        self.obj = obj
        self.loop = IOLoop.instance()
        # needs receive and send
        self.handler = wrapper.JSONRPC(obj, self, **kwargs)
        self.message = None
        logger.debug("done initialize")

    def receive(self):
        logger.debug("receive")
        return self.message

    def open(self):
        print("OH: open")
        logger.debug("Web socket opened")

    def on_close(self):
        print("OH: close")
        logger.debug("Web socket closed")
        # disconnect all signals
        self.handler.disconnect()

    def on_message(self, message):
        print("OH: on message\n%s" % str(message))
        logger.debug("Received message {}".format(message))
        self.message = message
        self.handler.update()
        self.message = None

    def send(self, message):
        print("OH: send\n%s" % str(message))
        logger.debug("Sending message {}".format(message))
        #self.write_message(message)
        # write_message must be called from ioloop
        self.loop.add_callback(self.write_message, message)
        logger.debug("Message written {}".format(message))


def register(obj, url=None, **kwargs):
    if url is None:
        url = 'ws'
    if kwargs is None:
        kwargs = {}
    if not hasattr(obj, '__wsrpc__'):
        try:
            s = wrapper.build_function_spec(obj)
            obj.__wsrpc__ = lambda spec=s: s
        except Exception as e:
            logger.error(
                "Failed to build function spec for object %s with %s", obj, e)
    kwargs['obj'] = obj
    obj_dict[url] = kwargs


def render_help():
    # return links for all registered objects
    page = "<html><head></head><body>"
    for n in server.blueprints:
        page += "<a href='/%s/'>%s</a><br />" % (
            n, n)
    page += "</body></html>"
    return page


def serve(address=None, default_route=None, port=5000):
    if address is None:
        address = ""
    if default_route is None:
        @server.route('/')
        def default():
            return render_help()
    else:
        @server.route('/')
        def default():
            return flask.redirect(default_route)
    wsgi_app = tornado.wsgi.WSGIContainer(server)
    items = []
    for k in obj_dict:
        items.append(('/{}'.format(k), ObjectHandler, obj_dict[k]))
    if 'help' not in k:
        @server.route('/help')
        def help():
            return render_help()
    items += [('.*', tornado.web.FallbackHandler, {'fallback': wsgi_app}), ]
    logger.debug("Serving items: {}".format(items))
    application = tornado.web.Application(items, debug=server.debug)
    application.listen(port, address=address)
    logger.info("Serving on address %s, port %s" % (address, port))
    loop = IOLoop.instance()
    if not loop._running:
        loop.start()
