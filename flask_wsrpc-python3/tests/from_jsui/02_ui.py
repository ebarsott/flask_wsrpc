#!/usr/bin/env python


import wsrpc
import pizco


class Foo(object):
    def __init__(self):
        self.msg = ""
        self.new_message = pizco.Signal(nargs=1)

        def blah(msg):
            print("new_message: {}".format(msg))

        self.new_message.connect(blah)

    def hi(self):
        print("hi")
        return "hi"

    def set_message(self, msg):
        if msg != self.msg:
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
        var new_message = function (msg) {
            console.log({'new_message': msg[0][0]});
            $('#msg').val(msg[0][0]);
        };
        var {{ name }};
        $(function () {
            {{ name }} = new RPCObject('{{ name }}');
            $({{ name }}).on('wsrpc_built', function () {

                {{ name }}.get_message().then(
                    function (msg) { $('#msg').val(msg); }, ecb);

                // there is no easy way to handle signals yet
                {{ name }}._socket.call(
                    'new_message.connect', [], new_message, ecb, true);

                $('#msg').on('change', function () {
                    {{ name }}.set_message($('#msg').val()).then(rcb, ecb);
                });
            });
        });
"""
html = """<input type="text" id="msg"></input>"""

template = """
<html>
    <head>
        <script src="{{url_for('static', filename='js/jquery-2.1.0.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/jquery.json-2.4.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/jquery.jsonrpcclient.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/bluebird.js')}}" type="text/javascript"></script>
        <script src="{{url_for('static', filename='js/rpcobject.js')}}" type="text/javascript"></script>
        {% if css is defined %}
            <style type="text/css">
            {{ css }}
            </style>
        {% endif %}
    </head>
    <body>
        {% if js is defined %}
            <script type="text/javascript">
            {{ js }}
            </script>
        {% endif %}
        {% if html is defined %}
            {{ html }}
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
        'html': html,
        'js': js,
    },
    {
        'name': 'b',
        'object': Foo(),
        'template': template,
        'html': html,
        'js': js,
    },
]

for s in specs:
    wsrpc.serve.register(s)

wsrpc.serve.serve()
