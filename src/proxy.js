pizco.proxy = function (addr) {
    /* -- proxy objects --
     * get
     * getattr
     * setattr
     * attr_as_remote, attr_as_obj = remote_inspect
     *
     * -- remote attributes --
     * get
     * set
     * getattr
     * setattr
     * call [requires javascript function]
     * getitem [requires javascript array]
     * setitem [requires javascript array]
     *
     * overload these with __defineGetter__ __defineSetter__ on top of a callable object (function)
     *
     * available (through proxy) server command
     *  inspect
     *  get
     *  getattr
     *  setattr
     *  exec
     */
    proxy = {};

    // open websocket to addr
    proxy._socket = new WebSocket(addr);

    // inspect remote object
    inspect = proxy._socket.send('inspect');
    console.log({'inspect': inspect});

    // return javascript function with overloaded getters & setters
};
