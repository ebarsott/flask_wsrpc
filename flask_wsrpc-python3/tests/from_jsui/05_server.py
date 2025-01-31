#!/usr/bin/env python

import concurrent.futures
import pizco


class Foo(object):
    def __init__(self):
        self.msg = ""
        self.new_message = pizco.Signal(nargs=1)
        self.loop = None
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def hi(self):
        print("hi")
        return "hi"

    def set_message(self, msg):
        self.msg = msg
        self.new_message.emit(self.msg)
        return "set_message"

    def set_message_in_loop(self, msg):
        self.loop.add_callback(self.set_message, msg)
        return "added set_message callback to loop"

    def set_message_in_pool(self, msg):
        self.pool.submit(self.set_message, msg)
        return "submitted set_message to pool"

    def set_message_in_pool_in_loop(self, msg):
        self.pool.submit(self.set_message_in_loop, msg)
        return "submitted set_message_in_loop to pool"

    def get_message(self):
        return self.msg


f = Foo()
s = pizco.Server(f, 'tcp://127.0.0.1:12345')
f.loop = s.loop
s.serve_forever()
