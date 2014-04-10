#!/usr/bin/env python
"""
Wrap an object with a json-rpc (v2) compatible interface
"""

import concurrent.futures

from . import errors
from . import protocol


def is_signal(o):
    return (
        hasattr(o, 'connect') and
        hasattr(o, 'disconnect') and
        hasattr(o, 'emit')
    )


def is_signal_message(m, o):
    if ('.' not in m['method']) and (not is_signal(o)):
        return False
    return is_signal(reduce(getattr, m['method'].split('.')[:-1], o))


class JSONRPC(object):
    def __init__(self, instance, socket, validate=True):
        """
        futures : list of functions that return a future object
        """
        self._i = instance
        self._v = validate
        for a in ['send', 'receive']:
            if (not hasattr(socket, a)):
                raise AttributeError(
                    "Invalid socket {} does not have {}".format(socket, a))
            if (not callable(getattr(socket, a))):
                raise AttributeError(
                    "Invalid socket {}, {} is not callable".format(socket, a))
        self._socket = socket
        self._signals = {}

    def _receive(self):
        m = self._socket.receive()
        try:
            dm = protocol.decode_request(m, validate=self._v)
            print("decoded {}".format(dm))
        except errors.RPCError as e:
            print("decode error {}".format(e))
            self._send(e)
            return None
        dm['id'] = dm.get('id', None)  # if there is no id, set to None
        return dm

    def _process(self, m):
        try:
            if '.' in m['method']:
                obj = reduce(getattr, m['method'].split('.')[:-1], self._i)
                method = m['method'].split('.')[-1]
            else:
                obj = self._i
                method = m['method']
            if (method == 'connect') and is_signal(obj):
                # generate a callback and attach it to the signal
                def cb(*args):
                    self._send(
                        {'jsonrpc': '2.0', 'result': args, 'id': m['id']})
                obj.connect(cb)
                # register this callback (and slot) with _signals
                self._signals[m['id']] = cb
                return dict(jsonrpc='2.0', result=m['id'], id=m['id'])
            elif (method == 'disconnect') and is_signal(obj):
                # find the callback and remove it
                # params should be id to remove
                if len(m['params']) != 1:
                    self._send(errors.ServerError(
                        'Invalid params {} expected 1 length array'.format(
                            m['params']), m['id']))
                cbid = m['params'][0]
                cb = self._signals[cbid]
                print 'before', obj.slots
                obj.disconnect(cb)
                print 'after', obj.slots
                del self._signals[cbid]
                # return success ?
                return dict(jsonrpc='2.0', result=None, id=m['id'])
            else:
                res = getattr(obj, method)(*m['params'])
        except Exception as e:
            print("call error {}".format(e))
            if m['id'] is None:
                return None  # notification
            self._send(errors.ServerError(repr(e), m['id']))
            return None
        if m['id'] is None:
            return None  # notification
        # check to see if res is a future, if so, attach callback
        if isinstance(res, concurrent.futures.Future):
            def cb(f):
                return self._send(dict(
                    jsonrpc='2.0', result=f.result(), id=m['id']))
            res.add_done_callback(cb)
            future = {'future': {'id': m['id']}}
            print("returning future {}".format(future))
            return dict(jsonrpc='2.0', result=future, id=m['id'])
        else:
            print("returning {}".format(res))
            return dict(jsonrpc='2.0', result=res, id=m['id'])

    def _send(self, m):
        if m is None:
            return
        # error handling?
        em = protocol.encode_response(m, validate=self._v)
        self._socket.send(em)

    def update(self):
        self._send(self._process(self._receive()))
