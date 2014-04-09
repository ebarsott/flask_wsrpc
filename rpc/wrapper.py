#!/usr/bin/env python
"""
Wrap an object with a json-rpc (v2) compatible interface
"""

from . import errors
from . import protocol


class JSONRPC(object):
    def __init__(self, instance, validate=True):
        self._i = instance
        self._v = validate

    def request(self, request):
        return protocol.process_request(request, self._i, self._v)
