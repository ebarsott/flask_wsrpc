#!/usr/bin/env python

import wsrpc


class Foo(object):
    def __init__(self):
        self.msg = ''

    def set_message(self, m):
        self.msg = m

    def get_message(self):
        return self.msg


wsrpc.serve.register(Foo())
wsrpc.serve.serve()
