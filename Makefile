JS_FILES = \
		src/head.js \
		src/protocol.js \
		src/proxy.js \
		src/tail.js

JS_COMPILER = \
		java -jar lib/google-compiler/compiler-20100616.jar \
		--charset UTF-8

#all: pizco.min.js pizco.js
all: pizco.js

#%.min.js: %.js
#	$(JS_COMPILER) < $^ > $@

#pizco.min.js: pizco.js
#	rm -rf $@
#	$(JS_COMPILER) < pizco.js >> $@

pizco.js: $(JS_FILES) Makefile
	rm -rf $@
	cat $(JS_FILES) >> $@
	chmod a-w $@

clean:
	rm -rf pizco.js pizco.min.js
