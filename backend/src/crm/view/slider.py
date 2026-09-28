#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request, g, current_app

from backend.src.crm.view import api_response, roles_required
from backend.src.crm.view.media import media_json
from backend.src.crm.view.validation import validate_display_fields
from backend.src.util import get_remote_ip
from backend.src.model import slider_access, media_access
from backend.src.model.enums import UserRole


bp = Blueprint('slider', __name__, url_prefix='/api')
log = logging.getLogger(__name__)


def _to_json(item):
    data = item.to_json()
    data['media'] = media_json(item.media)
    return data


@bp.route('/slider-items', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def slider_list():
    log.debug('%s - %s - %s: slider.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        return 'SUCCESS', [], [_to_json(i) for i in slider_access.list_all(search)]
    except Exception:
        log.exception('%s - %s: slider.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/slider-items/<int:item_id>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def slider_get(item_id):
    log.debug('%s - %s - %s: slider.get %s', get_remote_ip(), request.method, g.user.username, item_id)

    item = slider_access.get(item_id)
    if item is None:
        return 'ERROR', ['slider-not-found'], None
    return 'SUCCESS', [], _to_json(item)


@bp.route('/slider-items', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def slider_add():
    log.debug('%s - %s - %s: slider.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        fields = validate_display_fields(data, error_msg, 'slider')
        if error_msg:
            return 'ERROR', error_msg, None

        item = slider_access.add(fields, g.user.username)
        return 'SUCCESS', [], _to_json(item)
    except Exception:
        log.exception('%s - %s: slider.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/slider-items/<int:item_id>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def slider_edit(item_id):
    log.debug('%s - %s - %s: slider.edit %s', get_remote_ip(), request.method, g.user.username, item_id)

    error_msg = []
    try:
        item = slider_access.get(item_id)
        if item is None:
            return 'ERROR', ['slider-not-found'], None

        data = request.get_json() or {}
        fields = validate_display_fields(data, error_msg, 'slider')
        if error_msg:
            return 'ERROR', error_msg, None

        old_media_id = item.media_id
        item = slider_access.edit(item, fields, g.user.username)
        if old_media_id != item.media_id:
            media_access.delete_if_unused(old_media_id, current_app.config['MEDIA_UPLOAD_FOLDER'],
                                          g.user.username)
        return 'SUCCESS', [], _to_json(item)
    except Exception:
        log.exception('%s - %s: slider.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/slider-items/<int:item_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def slider_delete(item_id):
    log.debug('%s - %s - %s: slider.delete %s', get_remote_ip(), request.method, g.user.username, item_id)

    try:
        item = slider_access.get(item_id)
        if item is None:
            return 'ERROR', ['slider-not-found'], None

        media_id = item.media_id
        if not slider_access.delete(item, g.user.username):
            return 'ERROR', ['slider-not-found'], None
        media_access.delete_if_unused(media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: slider.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
