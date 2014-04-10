#!/usr/bin/env python

import json
import cPickle as pickle

import flask
import flask_sockets
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import pizco

app = flask.Flask(__name__)
app.debug = True
sockets = flask_sockets.Sockets(app)
proxy = pizco.clientserver.ProxyAgent('ipc:///tmp/pizcojs_test_rep')


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
    print('Connect proxy {} to websocket {}'.format(proxy, ws))
    while not ws.closed:
        gevent.sleep(0.001)
        m = ws.receive()
        print(m)
        if ws.closed or m is None:
            break
        p = json.loads(m)
        # TODO type & value checking
        cmd = p.keys()[0]
        arg = p[cmd]
        r = proxy.request_server(cmd, arg)  # TODO force as object
        print(r)
        r = fix_types(r)
        print(r)
        ws.send(json.dumps(r))


if __name__ == '__main__':
    # start background thread serving pizco events
    # this requires knowing which 'signals' to connect to
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
