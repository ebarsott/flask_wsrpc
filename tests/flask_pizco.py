#!/usr/bin/env python

import pizco

import rpc

proxy = pizco.Proxy('ipc:///tmp/pizcojs_test_rep')
rpc.serve.register(proxy)
rpc.serve.serve()
