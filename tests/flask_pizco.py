#!/usr/bin/env python

import pizco

import serve

proxy = pizco.Proxy('ipc:///tmp/pizcojs_test_rep')
serve.proxy = proxy
serve.run()
