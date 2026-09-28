#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import configparser
import logging
import os

from backend.src.crm import config

app = None

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')

def init_app():
    global app
    if app is None:
        con_parse = configparser.ConfigParser()
        con_parse.read(_CONFIG_PATH)

        app = config.app_create(__name__, con_parse)

init_app()
