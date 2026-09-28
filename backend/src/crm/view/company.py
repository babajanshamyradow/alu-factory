#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging
import re

from flask import Blueprint, request, g, current_app

from backend.src.crm.view import api_response, roles_required
from backend.src.crm.view.media import media_json
from backend.src.crm.view.validation import is_int, optional_str
from backend.src.util import get_remote_ip
from backend.src.model import company_access, company_image_access, media_access
from backend.src.model.enums import UserRole, MediaType


bp = Blueprint('company', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
# Digits with the usual separators, optionally starting with '+'.
PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{3,48}$')


def _to_json(company):
    data = company.to_json()
    data['logo'] = media_json(company.logo_media)
    data['cover'] = media_json(company.cover_media)
    return data


def _coordinate(value, limit, error_msg):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not -limit <= value <= limit:
        error_msg.append('company-coordinates-invalid')
        return None
    return round(value, 6)


def _image_id(data, key, error_code, error_msg):
    media_id = data.get(key)
    if media_id is None:
        return None
    media = media_access.get(media_id) if is_int(media_id) else None
    if media is None or media.media_type != MediaType.image:
        error_msg.append(error_code)
        return None
    return media_id


def _validate(data, error_msg):
    name = data.get('company-name')
    name = name.strip() if isinstance(name, str) else ''
    if not name or len(name) > 200:
        error_msg.append('company-name-invalid')

    email = optional_str(data, 'email', 255, 'company-email-invalid', error_msg)
    if email is not None and not EMAIL_RE.match(email):
        error_msg.append('company-email-invalid')
    phone = optional_str(data, 'phone', 50, 'company-phone-invalid', error_msg)
    if phone is not None and not PHONE_RE.match(phone):
        error_msg.append('company-phone-invalid')

    address = optional_str(data, 'address', 2000, 'company-address-invalid', error_msg)
    description = optional_str(data, 'description', 100000, 'company-description-invalid', error_msg)

    latitude = _coordinate(data.get('latitude'), 90, error_msg)
    longitude = _coordinate(data.get('longitude'), 180, error_msg)
    # A map pin needs both halves.
    if (latitude is None) != (longitude is None) and 'company-coordinates-invalid' not in error_msg:
        error_msg.append('company-coordinates-invalid')

    logo_media_id = _image_id(data, 'logo-media-id', 'company-logo-invalid', error_msg)
    cover_media_id = _image_id(data, 'cover-media-id', 'company-cover-invalid', error_msg)

    return {'company_name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'description': description,
            'latitude': latitude,
            'longitude': longitude,
            'logo_media_id': logo_media_id,
            'cover_media_id': cover_media_id}


@bp.route('/company', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def company_get():
    """The single company row, or no `result` when it is not created yet."""
    log.debug('%s - %s - %s: company.get', get_remote_ip(), request.method, g.user.username)

    try:
        company = company_access.get()
        return 'SUCCESS', [], _to_json(company) if company else None
    except Exception:
        log.exception('%s - %s: company.get error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_add():
    """Create the company info — allowed once; afterwards only PUT edits it."""
    log.debug('%s - %s - %s: company.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        if company_access.get() is not None:
            return 'ERROR', ['company-exists'], None

        data = request.get_json() or {}
        fields = _validate(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        company = company_access.add(fields, g.user.username)
        if company is None:
            return 'ERROR', ['company-exists'], None
        return 'SUCCESS', [], _to_json(company)
    except Exception:
        log.exception('%s - %s: company.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_edit():
    log.debug('%s - %s - %s: company.edit', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        company = company_access.get()
        if company is None:
            return 'ERROR', ['company-not-found'], None

        data = request.get_json() or {}
        fields = _validate(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        old_media_ids = {company.logo_media_id, company.cover_media_id} - {None}
        company = company_access.edit(company, fields, g.user.username)
        for media_id in old_media_ids - {company.logo_media_id, company.cover_media_id}:
            media_access.delete_if_unused(media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)
        return 'SUCCESS', [], _to_json(company_access.get())
    except Exception:
        log.exception('%s - %s: company.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


# ---------- Company gallery (tbl_company_image) ----------

def _image_to_json(image):
    data = image.to_json()
    data['media'] = media_json(image.media)
    return data


def _validate_image(data, error_msg, default_sort_order):
    media_id = _image_id(data, 'media-id', 'company-image-media-invalid', error_msg)
    if media_id is None and 'company-image-media-invalid' not in error_msg:
        error_msg.append('company-image-media-invalid')

    caption = optional_str(data, 'caption', 255, 'company-image-caption-invalid', error_msg)

    is_active = data.get('is-active', True)
    if not isinstance(is_active, bool):
        error_msg.append('company-image-is-active-invalid')
    sort_order = data.get('sort-order', default_sort_order)
    if not is_int(sort_order):
        error_msg.append('company-image-sort-order-invalid')

    return {'media_id': media_id,
            'caption': caption,
            'is_active': is_active,
            'sort_order': sort_order}


@bp.route('/company/images', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def company_image_list():
    log.debug('%s - %s - %s: company-image.list', get_remote_ip(), request.method, g.user.username)

    try:
        return 'SUCCESS', [], [_image_to_json(i) for i in company_image_access.list_all()]
    except Exception:
        log.exception('%s - %s: company-image.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company/images', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_image_add():
    """Add a gallery image; without `sort-order` it goes to the end."""
    log.debug('%s - %s - %s: company-image.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        fields = _validate_image(data, error_msg, company_image_access.next_sort_order())
        if error_msg:
            return 'ERROR', error_msg, None

        image = company_image_access.add(fields, g.user.username)
        return 'SUCCESS', [], _image_to_json(image)
    except Exception:
        log.exception('%s - %s: company-image.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company/images/order', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_image_reorder():
    """Body {"ids": [...]} — every gallery image id, in the new order."""
    log.debug('%s - %s - %s: company-image.reorder', get_remote_ip(), request.method, g.user.username)

    try:
        ids = (request.get_json() or {}).get('ids')
        if not isinstance(ids, list) or not all(is_int(i) for i in ids) or len(set(ids)) != len(ids):
            return 'ERROR', ['company-image-order-invalid'], None

        if not company_image_access.reorder(ids, g.user.username):
            return 'ERROR', ['company-images-modified'], None
        return 'SUCCESS', [], [_image_to_json(i) for i in company_image_access.list_all()]
    except Exception:
        log.exception('%s - %s: company-image.reorder error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company/images/<int:image_id>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_image_edit(image_id):
    log.debug('%s - %s - %s: company-image.edit %s', get_remote_ip(), request.method, g.user.username, image_id)

    error_msg = []
    try:
        image = company_image_access.get(image_id)
        if image is None:
            return 'ERROR', ['company-image-not-found'], None

        data = request.get_json() or {}
        fields = _validate_image(data, error_msg, image.sort_order)
        if error_msg:
            return 'ERROR', error_msg, None

        old_media_id = image.media_id
        image = company_image_access.edit(image, fields, g.user.username)
        if old_media_id != image.media_id:
            media_access.delete_if_unused(old_media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)
        return 'SUCCESS', [], _image_to_json(company_image_access.get(image_id))
    except Exception:
        log.exception('%s - %s: company-image.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/company/images/<int:image_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def company_image_delete(image_id):
    log.debug('%s - %s - %s: company-image.delete %s', get_remote_ip(), request.method, g.user.username, image_id)

    try:
        image = company_image_access.get(image_id)
        if image is None:
            return 'ERROR', ['company-image-not-found'], None

        media_id = image.media_id
        if not company_image_access.delete(image, g.user.username):
            return 'ERROR', ['company-image-not-found'], None
        media_access.delete_if_unused(media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: company-image.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
