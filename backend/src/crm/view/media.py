#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging
import os

from flask import Blueprint, request, g, current_app

from backend.src.crm.view import api_response, roles_required
from backend.src.util import get_remote_ip
from backend.src.model import media_access
from backend.src.model.enums import UserRole, MediaType


bp = Blueprint('media', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

MB = 1024 * 1024


def media_json(media):
    """Media JSON plus the URL the console/site can load it from."""
    if media is None:
        return None
    data = media.to_json()
    data['url'] = '/media/' + media.file_path
    return data


def _file_size(file_storage):
    stream = file_storage.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    return size


@bp.route('/media', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def media_upload():
    log.debug('%s - %s - %s: media.upload', get_remote_ip(), request.method, g.user.username)

    try:
        file_storage = request.files.get('file')
        if file_storage is None or not file_storage.filename:
            return 'ERROR', ['file-required'], None

        _, media_info = media_access.media_type_for(file_storage.filename)
        if media_info is None:
            return 'ERROR', ['file-type-not-allowed'], None

        max_mb = current_app.config['IMAGE_UPLOAD_MAX_SIZE_MB'] if media_info[0] == MediaType.image \
            else current_app.config['ANY_UPLOAD_MAX_SIZE_MB']
        if _file_size(file_storage) > max_mb * MB:
            return 'ERROR', ['file-too-large'], None

        alt_text = (request.form.get('alt-text') or '').strip()[:255] or None
        media = media_access.save_upload(file_storage, current_app.config['MEDIA_UPLOAD_FOLDER'],
                                         alt_text, g.user.username)
        if media is None:
            return 'ERROR', ['file-invalid'], None
        return 'SUCCESS', [], media_json(media)
    except Exception:
        log.exception('%s - %s: media.upload error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
