#!/usr/bin/env python
"""
"""

import os

import flask


if os.environ.get('WSRPC_USE_GEVENT', False):
    from . import geventserver as server
else:
    from . import tornadoserver as server


def rename(name):
    def wrap(func):
        func.func_name = name
        return func
    return wrap


def make_blueprint(spec):
    kwargs = {'url_prefix': '/{}'.format(spec['name'])}
    for k in ('static_folder', 'template_folder', 'static_url_path',
              'url_prefix'):
        if k in spec:
            kwargs[k] = spec[k]
    bp = flask.Blueprint(spec['name'], spec['name'], **kwargs)

    server.register(
        spec['object'], spec['name'] + '/ws',
        encoder=spec.get('encoder', None), decoder=spec.get('decoder', None))

    if 'css' in spec:
        @bp.route('/css')
        def css():
            return flask.render_template_string(spec['css'], **spec)
    if 'js' in spec:
        @bp.route('/js')
        def js():
            return flask.render_template_string(spec['js'], **spec)
    if 'html' in spec:
        @bp.route('/html')
        def html():
            return flask.render_template_string(spec['html'], **spec)
    if 'template' in spec:
        @bp.route('/')
        def template():
            local_spec = spec.copy()
            for item in ('css', 'js', 'html'):
                if item in spec:
                    local_spec[item] = flask.render_template_string(
                        spec[item], **spec)
            return flask.render_template_string(
                spec['template'], **local_spec)
    if 'template_folder' in spec:
        @bp.route('/templates/<template>')
        def named_template(template):
            return flask.render_template(template, **spec)
    return bp


def register(spec):
    bp = make_blueprint(spec)
    server.server.register_blueprint(bp)


def serve(address=None, default_route=True, debug=True):
    server.server.debug = debug
    server.serve(address, default_route)
