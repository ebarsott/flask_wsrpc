// requires bluebird.js

RPCObject = function (ws_url) {
    var self = this;
    var instance = {};
    instance._ws_url = ws_url;

    instance._build = function (functions) {
        // console.log({'build': functions});
        for (f in functions) {
            name = "";
            o = undefined;
            if (f.indexOf('.')) {
                str = f.split('.');
                o = instance;
                while (str.length > 1) {
                    n = str.shift();
                    if (o[n] == undefined) {
                        o[n] = {};
                    };
                    o = o[n];
                };
                name = str.shift();
            } else {
                name = f;
                o = instance;
            };
 
            // console.log({f: [typeof(f), f]});
            func = function (fn) {
                return function () {
                    args = Array.prototype.slice.call(arguments);
                    return new Promise(function (resolve, reject) {
                        // console.log({fn: args});
                        instance._socket.call(fn, args, resolve, reject);
                    });
                };
            }(f);

            // TODO handle signals?
            o[name] = func;
       };
        $(instance).trigger('wsrpc_built');
    };

    instance._connect = function () {
        if (instance._ws_url == undefined) {
            url = 'ws://' + window.location.host + '/ws';
        } else {
            url = 'ws://' + window.location.host + '/' + instance._ws_url + '/ws';
        };
        // console.log({'connect': url});
        instance._socket = new $.JsonRpcClient({'socketUrl': url});
        //instance._socket.call('__wsrpc__', [], function (r) { instance._build(r); }, instance._on_error);
        instance._socket.call('__wsrpc__', [], instance._build, instance._on_error);
        //instance._socket.call('__wsrpc__', [],
        //    function (r) { console.log({'r': r}); instance._build(r) }, instance._on_error);
        $(instance).trigger('wsrpc_connected');
    };

    instance._connect();

    return instance;
};
