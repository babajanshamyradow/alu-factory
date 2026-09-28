#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Public site API (read-only catalog + contact form) for the Vue site in frontend/."""

import logging
import logging.config
import os

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_CONF_PATH = os.path.join(_BACKEND_DIR, 'sip_logging.conf')

_prev_cwd = os.getcwd()
os.chdir(_BACKEND_DIR)
try:
    logging.config.fileConfig(_CONF_PATH)
finally:
    os.chdir(_prev_cwd)
log = logging.getLogger(__name__)

def run():
    logging.info('Starting Dev Server')
    from backend.src.sip.web import app
    app.config['DEBUG'] = True
    try:
        import uwsgi
        uwsgi.atexit = shutdown
    except ImportError:
        import atexit
        atexit.register(shutdown)
    app.run(host='127.0.0.1', port=app.config['PORT'])


def shutdown(*args, **kwargs):
    logging.info('Shutting down')


if __name__ == '__main__':
    run()
