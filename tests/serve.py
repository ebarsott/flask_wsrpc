#!/usr/bin/env python

import copy
import time

import concurrent.futures
import flask
import flask_sockets
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import pizco

import rpc

app = flask.Flask(__name__)
app.debug = True
sockets = flask_sockets.Sockets(app)


def add_dicts(a, b, modify=False):
    if not modify:
        a = copy.deepcopy(a)
    for k in b:
        if isinstance(b[k], dict):
            sa = a.get(k, {})
            if not isinstance(sa, dict):
                sa = {}
            a[k] = add_dicts(sa, b[k], modify=True)
        else:
            a[k] = b[k]
    return a


def wait():
    time.sleep(3)
    return "awake"


class Node(object):
    def __init__(self):
        self._config = {}

        self.config_changed = pizco.Signal(nargs=1)
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def config(self, config=None, replace=False):
        print("config {} {} {}".format(self._config, config, replace))
        if config is None:
            return self._config
        if replace:
            self._config = config
        else:
            self._config = add_dicts(self._config, config, modify=False)
        self.config_changed.emit(self._config)
        return self._config

    def future(self):
        return self._pool.submit(wait)

    def dosomething(self, a):
        print("doing stuff with {}".format(a))

proxy = Node()


@app.route('/')
def main():
    return flask.render_template('index.html')


@sockets.route('/echo')
def echo(ws):
    print('echo')
    for k in dir(ws):
        try:
            print('{} : {}'.format(k, getattr(ws, k)))
        except:
            pass
    while not ws.closed:
        m = ws.receive()
        print(m)
        if not ws.closed:
            ws.send(m)
    print('ws {} closed'.format(ws))


def fix_types(r):
    if isinstance(r, (dict, )):
        return dict([(k, fix_types(r[k])) for k in r])
    elif isinstance(r, (tuple, list, set)):
        return [fix_types(v) for v in r]
    return r


@sockets.route('/proxy')
def connect_proxy(ws):
    print('websocket connected {}'.format(ws))
    handler = rpc.wrapper.JSONRPC(proxy, ws)
    while not ws.closed:
        gevent.sleep(0.001)
        handler.update()


def run():
    # start background thread serving pizco events
    # this requires knowing which 'signals' to connect to
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == '__main__':
    run()
