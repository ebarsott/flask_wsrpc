#!/usr/bin/env python

import time
import threading

import flask
import flask.ext.socketio
import pizco

app = flask.Flask(__name__)
app.debug = True
socketio = flask.ext.socketio.SocketIO(app)
#proxy = pizco.Proxy('ipc:///tmp/pizcojs_test_rep')


@app.route('/')
def main():
    return flask.render_template('index.html')


@socketio.on('connect', namespace='/pizco')
def connect():
    print('connect')
    flask.ext.socketio.emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/pizco')
def disconnect():
    print('disconnect')


@socketio.on('foo', namespace='/pizco')
def foo(message):
    print('foo {}'.format(message))


if __name__ == '__main__':
    # start background thread serving pizco events
    # this requires knowing which 'signals' to connect to
    socketio.run(app)
