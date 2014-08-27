#!/usr/bin/env python
"""
error:
{'error': int # see error codes
'message': str # short description of error
'data': ...} # optional, additional data

error codes (negative):
    -32700 Parse Error
    -32600 Invalid Request
    -32601 Method not found
    -32602 Invalid params
    -32603 Internal error
    -32000 to -32099 Server error
"""


class RPCError(Exception):
    def __init__(self, message, code, msgid=None):
        Exception.__init__(self, message)
        self.code = code
        self.msgid = msgid

    def __str__(self):
        return '{}:{}:'.format(self.message, self.code, self.msgid)

    def __repr__(self):
        return '{}({}:{}:{})'.format(
            self.__class__.__name__, self.message, self.code, self.msgid)


class ParseError(RPCError):
    def __init__(self, message, msgid=None):
        RPCError.__init__(self, message, -32700, msgid)


class InvalidRequest(RPCError):
    def __init__(self, message, msgid=None):
        RPCError.__init__(self, message, -32600, msgid)


class MethodNotFound(RPCError):
    def __init__(self, message, msgid=None):
        RPCError.__init__(self, message, -32601, msgid)


class InvalidParams(RPCError):
    def __init__(self, message, msgid=None):
        RPCError.__init__(self, message, -32602, msgid)


class InternalError(RPCError):
    def __init__(self, message, msgid=None):
        RPCError.__init__(self, message, -32603, msgid)


class ServerError(RPCError):
    def __init__(self, message, msgid=None, code=-32000):
        if code > -32000 or code < -32099:
            raise ValueError(
                "Invalid ServerError code {} must be "
                "[-32099, -32000]".format(code))
        RPCError.__init__(self, message, code, msgid)
