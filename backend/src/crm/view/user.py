#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging
import re

from flask import Blueprint, request, g

from backend.src.crm.view import api_response, roles_required
from backend.src.util import get_remote_ip
from backend.src.model import user_access
from backend.src.model.enums import UserRole


bp = Blueprint('user', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]{3,64}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MIN_PASSWORD_LENGTH = 6


def _get_target_user(username):
    user = user_access.get_user(username)
    if user is None or user.username == 'SYSTEM':
        return None
    return user


def _parse_role(value):
    try:
        return UserRole(value)
    except ValueError:
        return None


def _validate_profile(data, error_msg):
    fullname = (data.get('fullname') or '').strip()
    email = (data.get('email') or '').strip() or None
    role = _parse_role(data.get('role'))

    if not fullname or len(fullname) > 64:
        error_msg.append('fullname-invalid')
    if email is not None and (len(email) > 256 or not EMAIL_RE.match(email)):
        error_msg.append('email-invalid')
    if role is None:
        error_msg.append('role-invalid')
    return fullname, email, role


@bp.route('/users', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def user_list():
    log.debug('%s - %s - %s: user.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        users = user_access.list_all(search)
        return 'SUCCESS', [], [u.to_json() for u in users]
    except Exception:
        log.exception('%s - %s: user.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/users/<username>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def user_get(username):
    log.debug('%s - %s - %s: user.get %s', get_remote_ip(), request.method, g.user.username, username)

    user = _get_target_user(username)
    if user is None:
        return 'ERROR', ['user-not-found'], None
    return 'SUCCESS', [], user.to_json()


@bp.route('/users', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def user_add():
    log.debug('%s - %s - %s: user.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}

        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        fullname, email, role = _validate_profile(data, error_msg)

        if not USERNAME_RE.match(username) or username.upper() == 'SYSTEM':
            error_msg.append('username-invalid')
        if len(password) < MIN_PASSWORD_LENGTH:
            error_msg.append('password-too-short')
        if error_msg:
            return 'ERROR', error_msg, None

        # Admins may create admins/operators, but not grant the superuser role.
        if g.user.role != UserRole.superuser and role == UserRole.superuser:
            return 'ERROR', ['permission-denied'], None

        user = user_access.add(username, fullname, password, role, email, g.user.username)
        if user is None:
            return 'ERROR', ['username-exists'], None
        return 'SUCCESS', [], user.to_json()
    except Exception:
        log.exception('%s - %s: user.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/users/<username>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def user_edit(username):
    log.debug('%s - %s - %s: user.edit %s', get_remote_ip(), request.method, g.user.username, username)

    error_msg = []
    try:
        user = _get_target_user(username)
        if user is None:
            return 'ERROR', ['user-not-found'], None

        data = request.get_json() or {}
        fullname, email, role = _validate_profile(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        # Admins may edit admins/operators, but never touch a superuser
        # account nor grant the superuser role.
        if g.user.role != UserRole.superuser and \
                (user.role == UserRole.superuser or role == UserRole.superuser):
            return 'ERROR', ['permission-denied'], None

        # Nobody changes their own role — avoids locking yourself out.
        if user.username == g.user.username and role != user.role:
            return 'ERROR', ['cannot-modify-self'], None

        if not user_access.edit(user, fullname, email, role, g.user.username):
            return 'ERROR', ['user-modified'], None
        return 'SUCCESS', [], _get_target_user(username).to_json()
    except Exception:
        log.exception('%s - %s: user.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/users/<username>/lock', methods=['PUT'])
@roles_required(UserRole.superuser)
@api_response
def user_lock(username):
    log.debug('%s - %s - %s: user.lock %s', get_remote_ip(), request.method, g.user.username, username)

    try:
        user = _get_target_user(username)
        if user is None:
            return 'ERROR', ['user-not-found'], None
        if user.username == g.user.username:
            return 'ERROR', ['cannot-modify-self'], None

        data = request.get_json() or {}
        locked = data.get('locked')
        if not isinstance(locked, bool):
            return 'ERROR', ['locked-invalid'], None

        if not user_access.set_locked(user, locked, g.user.username):
            return 'ERROR', ['user-modified'], None
        return 'SUCCESS', [], _get_target_user(username).to_json()
    except Exception:
        log.exception('%s - %s: user.lock error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/users/<username>/password', methods=['PUT'])
@roles_required(UserRole.superuser)
@api_response
def user_reset_password(username):
    log.debug('%s - %s - %s: user.reset-password %s', get_remote_ip(), request.method, g.user.username, username)

    try:
        user = _get_target_user(username)
        if user is None:
            return 'ERROR', ['user-not-found'], None

        data = request.get_json() or {}
        password = data.get('password') or ''
        if len(password) < MIN_PASSWORD_LENGTH:
            return 'ERROR', ['password-too-short'], None

        if not user_access.change_password(user, password, g.user.username):
            return 'ERROR', ['user-modified'], None
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: user.reset-password error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/users/<username>', methods=['DELETE'])
@roles_required(UserRole.superuser)
@api_response
def user_delete(username):
    log.debug('%s - %s - %s: user.delete %s', get_remote_ip(), request.method, g.user.username, username)

    try:
        user = _get_target_user(username)
        if user is None:
            return 'ERROR', ['user-not-found'], None
        if user.username == g.user.username:
            return 'ERROR', ['cannot-modify-self'], None

        if not user_access.delete(user, g.user.username):
            return 'ERROR', ['user-not-found'], None
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: user.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/profile/password', methods=['PUT'])
@roles_required()
@api_response
def profile_change_password():
    log.debug('%s - %s - %s: user.profile-password', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        old_password = data.get('old-password') or ''
        new_password = data.get('new-password') or ''

        if not user_access.verify_password(g.user.password, old_password):
            error_msg.append('old-password-invalid')
        if len(new_password) < MIN_PASSWORD_LENGTH:
            error_msg.append('password-too-short')
        if error_msg:
            return 'ERROR', error_msg, None

        if not user_access.change_password(g.user, new_password, g.user.username):
            return 'ERROR', ['user-modified'], None
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: user.profile-password error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
