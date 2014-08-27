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

import concurrent.futures

from . import errors


default_encoder = json.JSONEncoder
default_decoder = json.JSONDecoder


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
        check(not('error' in response), errors.ServerError,
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
def decode_request(request, validate=True, decoder=None):
    if decoder is None:
        decoder = default_decoder
    try:
        req = json.loads(request, cls=decoder)
    except Exception as e:
        raise errors.ParseError(repr(e))
    if validate:  # TODO handle validation errors
        validate_request(req)
    return req


def encode_error(error):
    r = dict(
        jsonrpc='2.0',
        error=dict(error=error.code, message=error.message), id=error.msgid)
    if hasattr(error, 'data'):
        r['error']['data'] = error['data']
    return r


# TODO make this batch compatible
def encode_response(response, validate=True, encoder=None):
    if isinstance(response, errors.RPCError):
        print("encoding error {}".format(response))
        return encode_response(
            encode_error(response), validate=validate, encoder=encoder)
    if validate:
        try:
            print("validating response {}".format(response))
            validate_response(response)
            print("valid")
        except errors.RPCError as e:
            print("invalid, sending error {}".format(e))
            return encode_response(e, validate=validate, encoder=encoder)
    if encoder is None:
        encoder = default_encoder
    try:
        print("dumping to json")
        return json.dumps(response, cls=encoder)
    except Exception as e:
        print("Error dumping to json {}".format(e))
        return encode_response(
            errors.ServerError(repr(e)), validate=validate, encoder=encoder)


# TODO make this batch compatible
# TODO break this apart to make attaching signals & futures easier?
def process_request(request, obj, validate=True, encoder=None, decoder=None):
    """
    This is quite broken up in rpc.wrapper
    """
    try:
        req = decode_request(request, validate=validate, decoder=decoder)
        print("decoded {}".format(req))
    except errors.RPCError as e:
        print("decode error {}".format(e))
        return encode_response(e, validate=validate, encoder=encoder)
    msgid = req.get('id', None)
    try:
        f = reduce(getattr, req['method'].split('.'), obj)
        # TODO handle signals
        print("calling {} with {}".format(f, req['params']))
        res = f(*tuple(req['params']))
        print("called {}".format(res))
    except Exception as e:
        print("call error {}".format(e))
        return encode_response(
            errors.ServerError(repr(e), msgid), validate=validate,
            encoder=encoder)
    if msgid is None:
        return  # notification, don't return
    # check to see if res is a future, if so, attach callback
    if isinstance(res, concurrent.futures.Future):
        def cb(f):
            return encode_response(dict(
                jsonrpc='2.0', result=f.result(), id=msgid), validate=validate,
                encoder=encoder)
        res.add_done_callback(cb)
        future = {'future': {'id': msgid}}
        print("returning future {}".format(future))
        return encode_response(dict(
            jsonrpc='2.0', result=future, id=msgid), validate=validate,
            encoder=encoder)
    else:
        print("returning {}".format(res))
        return encode_response(dict(
            jsonrpc='2.0', result=res, id=msgid), validate=validate,
            encoder=encoder)
