#!/usr/bin/env python
"""
Wrap an object with a json-rpc (v2) compatible interface

TODO have handler delete callbacks on __del__
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


def package_signal_result(signal, args, kwargs):
    # this does not work through a pizco Proxy as _... attributes are hidden
    has_args = (signal._varargs or signal._nargs)
    has_kwargs = (signal._varkwargs or len(signal._kwargs))
    if not (has_args or has_kwargs):
        return []
    if not has_args:
        return kwargs
    if signal._varargs is False and signal._nargs == 1:
        args = args[0]
    if not has_kwargs:
        return args
    return args, kwargs


class JSONRPC(object):
    def __init__(
            self, instance, socket, validate=True, encoder=None, decoder=None):
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
        self.encoder = encoder
        self.decoder = decoder

    def _receive(self):
        m = self._socket.receive()
        if m is None:  # this is a disconnect
            return m
        try:
            dm = protocol.decode_request(
                m, validate=self._v, decoder=self.decoder)
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
                if m['id'] is None:
                    return self._send(errors.ServerError(
                        'message id required for signal connection', m['id']))

                # generate a callback and attach it to the signal
                def cb(*args, **kwargs):
                    # TODO modify args and kwargs to match the function
                    # spec stored in the signal
                    print('signal callback {} with {}'.format(m['id'], args))
                    try:
                        self._send(
                            {'jsonrpc': '2.0',
                             'result': (args, kwargs),
                             'id': m['id']})
                    except Exception as e:
                        try:
                            self._send(errors.ServerError(
                                str(e), m['id']))
                        except Exception as e:
                            pass
                    print('signal callback done')
                print('connecting to signal {} with id {}'.format(
                    m['method'], m['id']))
                obj.connect(cb)
                # register this callback (and slot) with _signals
                self._signals[m['id']] = cb
                # TODO should the first message be the messageid?
                #return dict(jsonrpc='2.0', result=m['id'], id=m['id'])
                return None
            elif (method == 'disconnect') and is_signal(obj):
                # find the callback and remove it
                # params should be id to remove
                if len(m['params']) != 1:  # TODO instead disconnect all?
                    return self._send(errors.ServerError(
                        'Invalid params {} expected 1 length array'.format(
                            m['params']), m['id']))
                cbid = m['params'][0]
                print('disconnecting from signal {} with id {}'.format(
                    m['method'], cbid))
                cb = self._signals[cbid]
                #print 'before', obj.slots
                obj.disconnect(cb)
                #print 'after', obj.slots
                del self._signals[cbid]
                # TODO return success ?
                res = dict(jsonrpc='2.0', result=None, id=m['id'])
            else:
                res = getattr(obj, method)(*m.get('params', ()))
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
                self._send(dict(
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
        em = protocol.encode_response(
            m, validate=self._v, encoder=self.encoder)
        self._socket.send(em)

    def update(self):
        r = self._receive()
        print("received r: {}".format(r))
        if r is None:  # websocket disconnected
            return
        self._send(self._process(r))
