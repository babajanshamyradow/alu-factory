#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import json

from flask import Response, session, g
from functools import wraps

from backend.src.model import User


def roles_required(*roles):
    """Allow the endpoint only for logged-in users whose role is in `roles`.

    Roles are static (`UserRole` enum). The user is re-read from the DB on
    every request, so a lock or role change takes effect immediately instead
    of waiting for the session cookie to expire. With no `roles` given, any
    logged-in, unlocked user is allowed. The loaded user is exposed as
    `g.user` for the view.

    Must be placed above `@api_response`, since it returns bare 401/403
    responses rather than the JSON envelope:

        @bp.route('/api/users', methods=['GET'])
        @roles_required(UserRole.superuser, UserRole.admin)
        @api_response
        def user_list(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = session.get('u')
            user = User.query.get(username) if username else None
            if user is None or user.locked or user.username == 'SYSTEM':
                session.clear()
                return Response(status=401)

            if roles and user.role not in roles:
                return Response(status=403)

            g.user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator

def api_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        sync_permissions = False
        if 'sync-permissions' in kwargs:
            sync_permissions = kwargs['sync-permissions']
            del kwargs['sync-permissions']

        (status, error_msg, result) = f(*args, **kwargs)
        return json_response(status=status,
                             error_msg=error_msg,
                             result=result,
                             sync_permissions=sync_permissions)

    return decorated_function


def json_response(status, error_msg=None, result=None, sync_permissions=False):
    data = {'status': status}

    if sync_permissions:
        data['sync-permissions'] = sync_permissions

    if status == 'SUCCESS':
        if result:
            data['result'] = result
    elif status == 'MODIFIED':
        data['result'] = result
    elif status == 'NOT_ALLOWED':
        return Response(status=403)
    else:
        if error_msg:
            if 'permission-denied' in error_msg:
                return Response(status=403)
            else:
                data['error-msg'] = error_msg

    json_string = json.dumps(data, ensure_ascii=False)
    response = Response(json_string, content_type="application/json; charset=utf-8")
    return response


def api_file_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        (status, data, filename) = f(*args, **kwargs)
        return json_file_response(status=status,
                                  data=data,
                                  filename=filename)

    return decorated_function


def json_file_response(status, data, filename=None):
    if status == 'SUCCESS':
        status = 200
    elif status == 'ERROR':
        status = 500
    else:
        status = 503

    if status == 200:
        response = Response(data, status, mimetype="application/octet-stream",
                            headers={"Content-disposition": "attachment; filename=" + filename})
    else:
        data = {'status': "ERROR", 'error-msg': 'Error occured while generating request'}
        response = Response(json.dumps(data, ensure_ascii=False), status, content_type="application/json; charset=utf-8")
    return response

