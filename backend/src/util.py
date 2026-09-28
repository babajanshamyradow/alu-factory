#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from flask import request


def get_remote_ip():
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr
