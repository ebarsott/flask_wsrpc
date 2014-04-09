#!/usr/bin/env python

import copy

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


class Future(object):
    def __init__(self):
        self._done = False

    def done(self):
        if not self._done:
            self._done = True
            return False
        else:
            self._done = False
            return True

    # TODO add_done_callback?


class Node(object):
    def __init__(self):
        self._config = {}

        self.config_changed = pizco.Signal()

    def config(self, config=None, replace=False):
        if config is None:
            return self._config
        if replace:
            self._config = config
        else:
            self._config = add_dicts(self._config, config, modify=False)
        # TODO override, so no (new, old, other)
        self.config_changed.emit(self._config, None, None)
        return self._config

    def future(self):
        return Future()


s = pizco.Server(
    Node(), 'ipc:///tmp/pizcojs_test_rep', 'ipc:///tmp/pizcojs_test_pub')
s.serve_forever()
