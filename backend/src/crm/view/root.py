#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, Response, request, send_from_directory, session, current_app

from backend.src.crm.view import api_response
from backend.src.util import get_remote_ip
from backend.src.model import user_access


bp = Blueprint('root', __name__)
log = logging.getLogger(__name__)


@bp.route('/media/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config.get('MEDIA_UPLOAD_FOLDER'), filename)


@bp.route('/login', methods=['POST'])
@api_response
def login():
    log.debug('%s - %s: root.login', get_remote_ip(), request.method)

    status = 'ERROR'
    error_msg = []
    result = None

    try:
        request_data = request.get_json()

        username = request_data.get('username', '').strip()
        password = request_data.get('password', '').strip()

        user = user_access.login(username, password,
                                 ip_address=get_remote_ip(),
                                 user_agent=request.headers.get('User-Agent'))

        if user is not None and username != 'SYSTEM':
            # login successful, setup session
            session['u'] = user.username
            session['r'] = user.role.value
            session['l'] = user.lang.value

            session.permanent = True

            result = {'username': user.username,
                      'fullname': user.fullname,
                      'role': user.role.value,
                      'email': user.email,
                      'lang': user.lang.value}

            status = 'SUCCESS'
        else:
            error_msg = ["username-or-password-invalid"]

    except Exception:
        log.exception('%s - %s: root.login error', get_remote_ip(), request.method, exc_info=True)
        status = 'ERROR'
        error_msg = ['internal-server-error']
    return status, error_msg, result


@bp.route('/logout', methods=['GET'])
@api_response
def logout():
    log.debug('%s - %s - %s: root.logout', get_remote_ip(), request.method, session['u'] if 'u' in session else 'N/A')

    status = 'ERROR'
    error_msg = []
    result = None

    try:
        if 'u' in session:
            user_access.logout(session['u'],
                               ip_address=get_remote_ip(),
                               user_agent=request.headers.get('User-Agent'))

        session.pop('u', None)
        session.pop('r', None)
        session.pop('l', None)
        session.clear()

        status = 'SUCCESS'
    except Exception:
        log.exception('%s - %s: root.logout error', get_remote_ip(), request.method, exc_info=True)
        status = 'ERROR'
        error_msg = ['internal-server-error']
    return status, error_msg, result


@bp.route('/auth-check', methods=['GET'])
def auth_check():
    username = session.get('u')
    if not username:
        log.debug('%s - %s: root.auth-check no session', get_remote_ip(), request.method)
        return Response(status=401)

    user = user_access.get_user(username)
    if user is None:
        log.debug('%s - %s: root.auth-check user not found: %s', get_remote_ip(), request.method, username)
        return Response(status=401)

    if user.locked:
        log.debug('%s - %s: root.auth-check user locked: %s', get_remote_ip(), request.method, username)
        return Response(status=401)

    response = Response(status=200)
    response.headers['X-User-Id'] = user.username
    return response


@bp.route('/me', methods=['GET'])
@api_response
def me():
    log.debug('%s - %s: root.me', get_remote_ip(), request.method)

    status = 'ERROR'
    error_msg = []
    result = None

    username = session.get('u')
    if username:
        user = user_access.get_user(username)
        if user is not None and not user.locked:
            result = {'username': user.username,
                      'fullname': user.fullname,
                      'role': user.role.value,
                      'email': user.email,
                      'lang': user.lang.value}
            status = 'SUCCESS'
        else:
            session.clear()
            error_msg = ['not-authenticated']
    else:
        error_msg = ['not-authenticated']

    return status, error_msg, result
