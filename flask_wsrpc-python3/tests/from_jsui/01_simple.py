#!/usr/bin/env python


import wsrpc
import pizco


class Foo(object):
    def __init__(self):
        self.msg = ""
        self.new_message = pizco.Signal(nargs=1)

    def hi(self):
        print("hi")
        return "hi"

    def set_message(self, msg):
        self.msg = msg
        self.new_message.emit(self.msg)

    def get_message(self):
        return self.msg


js = """
        var ecb = function (e) {
            console.log({'error': e});
        };
        var rcb = function (r) {
            console.log({'result': r});
        };
        var {{ name }};
        $(function () {
            {{ name }} = new RPCObject('{{ name }}');
        });
"""

template = """
<html>
    <head>
        <script src="{{url_for('static', filename='js/jquery-2.1.0.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/jquery.json-2.4.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/jquery.jsonrpcclient.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/bluebird.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/rpcobject.js')}}" type="text/javascript"></script>
    </head>
    <body>
        {% if js is defined %}
            <script type="text/javascript">
            {{ js }}
            </script>
        {% endif %}
    </body>
</html>
"""


specs = [
    {
        'name': 'a',
        'object': Foo(),
        #'encoder': ,
        #'decoder': ,
        'template': template,
        #'css': ,
        #'html': ,
        'js': js,
    },
    {
        'name': 'b',
        'object': Foo(),
        'template': template,
        'js': js
    },
]

for s in specs:
    wsrpc.serve.register(s)

wsrpc.serve.serve()
