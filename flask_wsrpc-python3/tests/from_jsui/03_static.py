#!/usr/bin/env python

import os

import wsrpc


class Hi(object):
    pass


base = os.path.dirname(os.path.abspath(__file__))
static = os.path.join(base, '03', 'static')
templates = os.path.join(base, '03', 'templates')

if not os.path.exists(static):
    print("Failed to find the static folder {}".format(static))
    print("Perhaps this wasn't run from the tests subdirectory?")
    raise Exception("Failed to find static folder {}".format(static))

wsrpc.serve.register({
    'name': 'hi',
    'object': Hi(),
    'static_folder': static,
    'template_folder': templates,
})
print("Go to http://127.0.0.1:5000/hi/templates/hi.html")
wsrpc.serve.serve()
