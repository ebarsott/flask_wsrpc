#!/usr/bin/env python

import pizco

import serve


s = pizco.Server(
    serve.Node(), 'ipc:///tmp/pizcojs_test_rep', 'ipc:///tmp/pizcojs_test_pub')
s.serve_forever()
