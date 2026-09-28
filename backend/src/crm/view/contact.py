#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request, g

from backend.src.crm.view import api_response, roles_required
from backend.src import contact_form
from backend.src.util import get_remote_ip
from backend.src.model import contact_access
from backend.src.model.enums import UserRole, ContactStatus


bp = Blueprint('contact', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def _to_json(message, full=False):
    data = message.to_json()
    if full:
        data['ip-address'] = message.ip_address
        data['user-agent'] = message.user_agent
    return data


def _positive_int_arg(name, default):
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


@bp.route('/contact-messages', methods=['POST'])
@api_response
def contact_submit():
    """Public endpoint for the website's contact form — no login required."""
    return contact_form.submit_from_request()


@bp.route('/contact-messages', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def contact_list():
    log.debug('%s - %s - %s: contact.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        try:
            status = ContactStatus(request.args.get('status'))
        except ValueError:
            status = None
        page = _positive_int_arg('page', 1)
        per_page = min(_positive_int_arg('per-page', DEFAULT_PER_PAGE), MAX_PER_PAGE)

        messages, total = contact_access.list_page(search, status, page, per_page)
        return 'SUCCESS', [], {'items': [_to_json(m) for m in messages],
                               'total': total,
                               'page': page,
                               'per-page': per_page,
                               'counts': contact_access.status_counts()}
    except Exception:
        log.exception('%s - %s: contact.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/contact-messages/counts', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def contact_counts():
    """Per-status counts — polled by the console for the "new" menu badge."""
    try:
        return 'SUCCESS', [], contact_access.status_counts()
    except Exception:
        log.exception('%s - %s: contact.counts error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/contact-messages/<int:message_id>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def contact_get(message_id):
    log.debug('%s - %s - %s: contact.get %s', get_remote_ip(), request.method, g.user.username, message_id)

    message = contact_access.get(message_id)
    if message is None:
        return 'ERROR', ['contact-not-found'], None
    return 'SUCCESS', [], _to_json(message, full=True)


@bp.route('/contact-messages/<int:message_id>/status', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def contact_set_status(message_id):
    """The customer's text is never edited — only its processing status."""
    log.debug('%s - %s - %s: contact.status %s', get_remote_ip(), request.method, g.user.username, message_id)

    try:
        message = contact_access.get(message_id)
        if message is None:
            return 'ERROR', ['contact-not-found'], None

        try:
            status = ContactStatus((request.get_json() or {}).get('status'))
        except ValueError:
            return 'ERROR', ['contact-status-invalid'], None

        message = contact_access.set_status(message, status, g.user.username)
        return 'SUCCESS', [], _to_json(message, full=True)
    except Exception:
        log.exception('%s - %s: contact.status error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/contact-messages/<int:message_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def contact_delete(message_id):
    log.debug('%s - %s - %s: contact.delete %s', get_remote_ip(), request.method, g.user.username, message_id)

    try:
        message = contact_access.get(message_id)
        if message is None:
            return 'ERROR', ['contact-not-found'], None
        if not contact_access.delete(message, g.user.username):
            return 'ERROR', ['contact-not-found'], None
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: contact.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
