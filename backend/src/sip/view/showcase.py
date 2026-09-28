#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Home page slider and promo banners — only what is active right now."""

import logging

from datetime import datetime

from flask import Blueprint, request

from backend.src.crm.view.media import media_json
from backend.src.sip.view import api_response
from backend.src.util import get_remote_ip
from backend.src.model import slider_access, banner_access


bp = Blueprint('showcase', __name__, url_prefix='/api')
log = logging.getLogger(__name__)


def _item_json(item):
    return {'id': item.id,
            'title': item.title,
            'subtitle': item.subtitle,
            'link-url': item.link_url,
            'media': media_json(item.media)}


def _visible_product(product):
    """Link a banner to its product only while visitors can open it."""
    if product is None or not product.is_active or not product.category.is_active:
        return None
    return {'id': product.id, 'name': product.name, 'slug': product.slug}


@bp.route('/slider', methods=['GET'])
@api_response
def slider_list():
    log.debug('%s - %s: site.slider', get_remote_ip(), request.method)

    try:
        return 'SUCCESS', [], [_item_json(i) for i in slider_access.list_public(datetime.utcnow())]
    except Exception:
        log.exception('%s - %s: site.slider error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/banners', methods=['GET'])
@api_response
def banner_list():
    log.debug('%s - %s: site.banners', get_remote_ip(), request.method)

    try:
        result = []
        for banner in banner_access.list_public(datetime.utcnow()):
            data = _item_json(banner)
            data['product'] = _visible_product(banner.product)
            result.append(data)
        return 'SUCCESS', [], result
    except Exception:
        log.exception('%s - %s: site.banners error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
