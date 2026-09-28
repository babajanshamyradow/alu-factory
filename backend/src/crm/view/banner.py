#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request, g, current_app

from backend.src.crm.view import api_response, roles_required
from backend.src.crm.view.media import media_json
from backend.src.crm.view.product import product_brief
from backend.src.crm.view.validation import validate_display_fields, is_int
from backend.src.util import get_remote_ip
from backend.src.model import banner_access, media_access, product_access
from backend.src.model.enums import UserRole


bp = Blueprint('banner', __name__, url_prefix='/api')
log = logging.getLogger(__name__)


def _to_json(banner):
    data = banner.to_json()
    data['media'] = media_json(banner.media)
    data['product'] = product_brief(banner.product)
    return data


def _validate(data, error_msg):
    fields = validate_display_fields(data, error_msg, 'banner')

    # Optional: the banner may advertise a product.
    product_id = data.get('product-id')
    if product_id is not None and (not is_int(product_id) or product_access.get(product_id) is None):
        error_msg.append('banner-product-invalid')
    fields['product_id'] = product_id
    return fields


@bp.route('/banners', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def banner_list():
    log.debug('%s - %s - %s: banner.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        return 'SUCCESS', [], [_to_json(b) for b in banner_access.list_all(search)]
    except Exception:
        log.exception('%s - %s: banner.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/banners/<int:banner_id>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def banner_get(banner_id):
    log.debug('%s - %s - %s: banner.get %s', get_remote_ip(), request.method, g.user.username, banner_id)

    banner = banner_access.get(banner_id)
    if banner is None:
        return 'ERROR', ['banner-not-found'], None
    return 'SUCCESS', [], _to_json(banner)


@bp.route('/banners', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def banner_add():
    log.debug('%s - %s - %s: banner.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        fields = _validate(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        banner = banner_access.add(fields, g.user.username)
        return 'SUCCESS', [], _to_json(banner)
    except Exception:
        log.exception('%s - %s: banner.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/banners/<int:banner_id>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def banner_edit(banner_id):
    log.debug('%s - %s - %s: banner.edit %s', get_remote_ip(), request.method, g.user.username, banner_id)

    error_msg = []
    try:
        banner = banner_access.get(banner_id)
        if banner is None:
            return 'ERROR', ['banner-not-found'], None

        data = request.get_json() or {}
        fields = _validate(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        old_media_id = banner.media_id
        banner = banner_access.edit(banner, fields, g.user.username)
        if old_media_id != banner.media_id:
            media_access.delete_if_unused(old_media_id, current_app.config['MEDIA_UPLOAD_FOLDER'],
                                          g.user.username)
        return 'SUCCESS', [], _to_json(banner)
    except Exception:
        log.exception('%s - %s: banner.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/banners/<int:banner_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def banner_delete(banner_id):
    log.debug('%s - %s - %s: banner.delete %s', get_remote_ip(), request.method, g.user.username, banner_id)

    try:
        banner = banner_access.get(banner_id)
        if banner is None:
            return 'ERROR', ['banner-not-found'], None

        media_id = banner.media_id
        if not banner_access.delete(banner, g.user.username):
            return 'ERROR', ['banner-not-found'], None
        media_access.delete_if_unused(media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: banner.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
