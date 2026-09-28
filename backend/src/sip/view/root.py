#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from flask import Blueprint, send_from_directory, current_app


bp = Blueprint('root', __name__)


@bp.route('/media/<path:filename>')
def uploaded_file(filename):
    response = send_from_directory(current_app.config.get('MEDIA_UPLOAD_FOLDER'), filename)
    # Uploads get a fresh filename on every upload, so they never change in place.
    response.cache_control.public = True
    response.cache_control.max_age = 7 * 24 * 3600
    return response
