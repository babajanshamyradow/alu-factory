#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request

from backend.src.crm.view.media import media_json
from backend.src.sip.view import api_response
from backend.src.util import get_remote_ip
from backend.src.model import company_access, company_image_access


bp = Blueprint('company', __name__, url_prefix='/api')
log = logging.getLogger(__name__)


@bp.route('/company', methods=['GET'])
@api_response
def company_get():
    """Company info + active gallery. `result` is absent until the admin
    fills in the company in the console."""
    log.debug('%s - %s: site.company', get_remote_ip(), request.method)

    try:
        company = company_access.get()
        if company is None:
            return 'SUCCESS', [], None

        data = company.to_json()
        data['logo'] = media_json(company.logo_media)
        data['cover'] = media_json(company.cover_media)
        data['gallery'] = [{'id': image.id,
                            'caption': image.caption,
                            'media': media_json(image.media)}
                           for image in company_image_access.list_active()]
        return 'SUCCESS', [], data
    except Exception:
        log.exception('%s - %s: site.company error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
