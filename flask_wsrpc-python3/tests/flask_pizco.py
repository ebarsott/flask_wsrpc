#!/usr/bin/env python

import pizco

import wsrpc

proxy = pizco.Proxy('ipc:///tmp/pizcojs_test_rep')
wsrpc.serve.register(proxy)
wsrpc.serve.serve()
