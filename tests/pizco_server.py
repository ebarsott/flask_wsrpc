#!/usr/bin/env python

import copy
import time

import concurrent.futures

import pizco


def add_dicts(a, b, modify=False):
    if not modify:
        a = copy.deepcopy(a)
    for k in b:
        if isinstance(b[k], dict):
            sa = a.get(k, {})
            if not isinstance(sa, dict):
                sa = {}
            a[k] = add_dicts(sa, b[k], modify=True)
        else:
            a[k] = b[k]
    return a


def wait():
    time.sleep(3)
    return "awake"


class Node(object):
    def __init__(self):
        self._config = {}

        self.config_changed = pizco.Signal(nargs=1)
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def config(self, config=None, replace=False):
        print("config {} {} {}".format(self._config, config, replace))
        if config is None:
            return self._config
        if replace:
            self._config = config
        else:
            self._config = add_dicts(self._config, config, modify=False)
        self.config_changed.emit(self._config)
        return self._config

    def future(self):
        return self._pool.submit(wait)

    def dosomething(self, a):
        print("doing stuff with {}".format(a))


s = pizco.Server(
    Node(), 'ipc:///tmp/pizcojs_test_rep', 'ipc:///tmp/pizcojs_test_pub')
s.serve_forever()
