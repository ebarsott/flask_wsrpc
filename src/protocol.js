pizco.protocol = function () {
    /*
     * Protocol layout
     *
     * Frame 0: Header (utf-8 str)
     *  + separated
     *      1) protocol version
     *      2) unique id of sender
     *      3) string specifying the topic
     *  example: PZC00+urn:uuid:ad2d9eb0-c5f8-4bfb-a37d-6b7903b041f3+value_changed
     *
     * Frame 1: Serialization (utf-8 str)
     *  pickle, pickleN or json
     *
     * Frame 2: Content (binary blob)
     * 
     * Frame 3: Message ID (utf-8 str)
     *  unique id of message
     *  example: urn:uuid:b711f2b8-277d-40df-a283-6269331db251
     *
     * Frame 4: Signature (bytes)
     *  HMAC sha1
     */
};
