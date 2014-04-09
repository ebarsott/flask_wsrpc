#!/usr/bin/env python
"""
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

import json

from . import errors


def check(b, e, m, msgid=None, c=None):
    if not b:
        if c is None:
            raise e(m, msgid=msgid)
        else:
            raise e(m, msgid=msgid, code=c)


# TODO make this batch compatible
def validate_request(request):
    if 'id' in request:
        check(isinstance(request['id'], (int, str, unicode, type(None))),
              errors.InvalidRequest, 'invalid id type {}'.format(
                  type(request['id'])), None)
    msgid = request.get('id', None)
    check('jsonrpc' in request, errors.InvalidRequest,
          'request {} missing jsonrpc'.format(request), msgid)
    check(
        request['jsonrpc'] == '2.0',
        errors.InvalidRequest,
        'received non v2.0 [{}] request'.format(request['jsonrpc']), msgid)
    check('method' in request, errors.InvalidRequest,
          'request {} missing method'.format(request), msgid)
    check(isinstance(request['method'], (str, unicode)),
          errors.InvalidRequest,
          'request method {} is not a str'.format(request['method']), msgid)
    for k in request:
        if k not in ['jsonrpc', 'method', 'params', 'id']:
            raise errors.InvalidRequest(
                'Invalid key {} in request {}'.format(k, request), msgid)


# TODO make this batch compatible
# TODO add specific server error codes
def validate_response(response):
    check('id' in response, errors.ServerError,
          'response {} missing id'.format(response), None)
    check(isinstance(response['id'], (int, str, unicode, type(None))),
          errors.ServerError,
          'invalid id type {}'.format(type(response['id'])), None)
    msgid = response['id']
    check('jsonrpc' in response, errors.ServerError,
          'response {} missing jsonrpc'.format(response), msgid)
    check(
        response['jsonrpc'] == '2.0',
        errors.ServerError,
        'received non v2.0 [{}] response'.format(response['jsonrpc']),
        msgid)
    if 'error' in response:
        check(not('result' in response), errors.ServerError,
              'response {} contains both error and result'.format(
                  response), msgid)
        e = response['error']
        check('error' in e, errors.ServerError,
              'response error {} missing code'.format(e), msgid)
        check(isinstance(e['error'], int), errors.ServerError,
              'response error {} is not an int'.format(e['error']), msgid)
        check('message' in e, errors.ServerError,
              'response error {} missing message'.format(e), msgid)
        check(isinstance(e['message'], (str, unicode)), errors.ServerError,
              'response error {} is not a str'.format(e['message']), msgid)
        for k in e:
            if k not in ['error', 'message', 'data']:
                raise errors.ServerError(
                    'Invalid key {} in response error {}'.format(k, e),
                    msgid)
    elif 'result' in response:
        check(not('result' in response), errors.ServerError,
              'response {} contains both error and result'.format(
                  response), msgid)
    else:
        raise errors.ServerError(
            'response {} contains neither error nor result'.format(
                response), msgid)
    for k in response:
        if k not in ['jsonrpc', 'result', 'error', 'id']:
            raise errors.ServerError(
                'Invalid key {} in response {}'.format(k, response), msgid)


# TODO make this batch compatible
def decode_request(request, validate=True):
    try:
        req = json.loads(request)
    except Exception as e:
        raise errors.ParseError(repr(e))
    if validate:  # TODO handle validation errors
        validate_request(req)
    return req


def encode_error(error):
    r = dict(
        jsonrpc='2.0',
        error=dict(error=error.code, message=error.message, id=error.msgid))
    if hasattr(error, 'data'):
        r['error']['data'] = error['data']
    return r


# TODO make this batch compatible
def encode_response(response, validate=True):
    if isinstance(response, errors.RPCError):
        return encode_response(encode_error(response), validate=validate)
    if validate:
        try:
            validate_response(response)
        except errors.RPCError as e:
            return encode_response(
                encode_error(e), validate=validate)
    try:
        return json.dumps(response)
    except Exception as e:
        return encode_response(errors.ServerError(repr(e)), validate=validate)


# TODO make this batch compatible
# TODO break this apart to make attaching signals & futures easier?
def process_request(request, obj, validate=True):
    try:
        req = decode_request(request, validate=validate)
    except errors.RPCError as e:
        return encode_response(e, validate=validate)
    try:
        f = reduce(getattr, request['method'].split('.'), obj)
        res = f(request['params'])
    except Exception as e:
        return errors.ServerError(repr(e), req['id'])
    return encode_response(res, validate=validate)
