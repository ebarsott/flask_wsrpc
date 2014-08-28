#!/usr/bin/env python
"""
Wrap an object with a json-rpc (v2) compatible interface

JSON RPC v2

1) Requests
{'jsonrpc': '2.0' # always
'method': 'name' # required
'params': ... # optional
'id': str/int} # optinal, if not included, assumed to be a notification

2) Responses
{'jsonrpc': '2.0' #
'result': ... # only if no error
'error': see below # only if no result
'id': str/int} # same as request or null on parse error

error:
{'error': int # see error codes
'message': str # short description of error
'data': ...} # optional, additional data

3) Batch
array of requests, return is array of responses (except for notifications)
return order doesn't matter, processing order doesn't matter
client must match responses to requests by id
on batch processing failure, return single response
on empty array (all notifications), return nothing

error codes (negative):
    -32700 Parse Error
    -32600 Invalid Request
    -32601 Method not found
    -32602 Invalid params
    -32603 Internal error
    -32000 to -32099 Server error
"""

import os

from . import errors
from . import protocol
from . import wrapper

if os.environ.get('WSRPC_USE_GEVENT', False):
    from . import geventserver as serve
else:
    from . import tornadoserver as serve

from .protocol import process_request

__version__ = '0.0.2'

__all__ = ['errors', 'protocol', 'wrapper', 'serve', 'process_request']
