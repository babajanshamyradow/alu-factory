#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Public contact form: validation, anti-spam and submit — shared by the
CRM (crm/view/contact.py) and the public site API (sip/view/contact.py)."""

import logging
import re

from flask import request, current_app

from backend.src.crm.view.validation import optional_str
from backend.src.util import get_remote_ip
from backend.src.model import contact_access

log = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{3,48}$')
MAX_MESSAGE_LENGTH = 5000
RATE_LIMIT_WINDOW_SECONDS = 3600
# Hidden form field real visitors never fill in; bots usually do.
HONEYPOT_FIELD = 'website'


def _rate_limited(ip_address):
    """True when this IP already sent CONTACT_RATE_LIMIT_PER_HOUR messages
    in the current window. A Redis outage must not block real customers,
    so errors fail open (logged)."""
    limit = current_app.config['CONTACT_RATE_LIMIT_PER_HOUR']
    key = '%s:contact-rate:%s' % (current_app.config.get('REDIS_PREFIX') or 'alufactory', ip_address)
    try:
        count = current_app.redis.incr(key)
        if count == 1:
            current_app.redis.expire(key, RATE_LIMIT_WINDOW_SECONDS)
        return count > limit
    except Exception:
        log.exception('Contact rate limit check failed for %s', ip_address)
        return False


def _validate_submission(data, error_msg):
    name = data.get('name')
    name = name.strip() if isinstance(name, str) else ''
    if not name or len(name) > 150:
        error_msg.append('contact-name-invalid')

    email = optional_str(data, 'email', 255, 'contact-email-invalid', error_msg)
    if email is not None and not EMAIL_RE.match(email):
        error_msg.append('contact-email-invalid')
    phone = optional_str(data, 'phone', 50, 'contact-phone-invalid', error_msg)
    if phone is not None and not PHONE_RE.match(phone):
        error_msg.append('contact-phone-invalid')
    # Mirrors ck_contact_message_email_or_phone.
    if email is None and phone is None and not {'contact-email-invalid', 'contact-phone-invalid'} & set(error_msg):
        error_msg.append('contact-email-or-phone-required')

    message = data.get('message')
    message = message.strip() if isinstance(message, str) else ''
    if not message or len(message) > MAX_MESSAGE_LENGTH:
        error_msg.append('contact-message-invalid')

    return {'name': name, 'email': email, 'phone': phone, 'message': message}


def submit_from_request():
    """Handle a contact form POST; returns the (status, error_msg, result)
    triple expected by `api_response`."""
    ip_address = get_remote_ip()
    log.debug('%s - %s: contact.submit', ip_address, request.method)

    error_msg = []
    try:
        data = request.get_json(silent=True) or {}

        # Pretend success so bots don't learn to skip the field.
        if data.get(HONEYPOT_FIELD):
            log.info('%s: contact.submit honeypot filled, dropped', ip_address)
            return 'SUCCESS', [], None

        fields = _validate_submission(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        if _rate_limited(ip_address):
            return 'ERROR', ['contact-rate-limited'], None

        contact_access.submit(fields, ip_address, request.headers.get('User-Agent'))
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: contact.submit error', ip_address, request.method)
        return 'ERROR', ['internal-server-error'], None
