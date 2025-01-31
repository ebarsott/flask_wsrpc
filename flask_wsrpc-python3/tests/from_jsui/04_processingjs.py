#!/usr/bin/env python

import os

import wsrpc
import pizco


class Joy2d(object):
    def __init__(self):
        self.x = 0.
        self.y = 0.
        self.new_location = pizco.Signal(nargs=2)

    def get_location(self):
        print("get_location")
        return self.x, self.y

    def set_location(self, x, y):
        print("set_location: {}, {}".format(x, y))
        if (self.x == x) and (self.y == y):
            return
        self.x = x
        self.y = y
        print("new_location.emit: {}, {}".format(x, y))
        self.new_location.emit(x, y)

    def move(self, x, y, relative=False):
        print("move: {}, {}, {}".format(x, y, relative))
        if relative:
            self.set_location(self.x + x, self.y + y)
        else:
            self.set_location(x, y)


base = os.path.dirname(os.path.abspath(__file__))
static = os.path.join(base, '04', 'static')
templates = os.path.join(base, '04', 'templates')

if not os.path.exists(static):
    print("Failed to find the static folder {}".format(static))
    print("Perhaps this wasn't run from the tests subdirectory?")
    raise Exception("Failed to find static folder {}".format(static))

wsrpc.serve.register({
    'name': 'joy2d',
    'object': Joy2d(),
    'static_folder': static,
    'template_folder': templates,
})
print("Go to http://127.0.0.1:5000/joy2d/templates/joy2d.html")
wsrpc.serve.serve()
