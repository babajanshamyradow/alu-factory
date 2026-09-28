#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Public product catalog: active categories and active products only."""

import logging

from flask import Blueprint, request

from backend.src.crm.view.media import media_json
from backend.src.sip.view import api_response
from backend.src.util import get_remote_ip
from backend.src.model import category_access, product_access


bp = Blueprint('catalog', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

DEFAULT_PER_PAGE = 12
MAX_PER_PAGE = 48
MAX_SEARCH_LENGTH = 100
RELATED_LIMIT = 4


def _positive_int_arg(name, default):
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _category_json(category):
    return {'id': category.id, 'name': category.name, 'slug': category.slug}


def _card_json(product, images):
    """Product card for grids: cover image only."""
    return {'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'short-description': product.short_description,
            'is-featured': product.is_featured,
            'category': _category_json(product.category),
            'cover': media_json(images[0].media) if images else None}


def _cards(products):
    images = product_access.images_of([p.id for p in products])
    return [_card_json(p, images.get(p.id, [])) for p in products]


@bp.route('/categories', methods=['GET'])
@api_response
def category_list():
    log.debug('%s - %s: site.categories', get_remote_ip(), request.method)

    try:
        categories = category_access.list_public()
        counts = category_access.active_product_counts([c.id for c in categories])
        result = []
        for category in categories:
            data = _category_json(category)
            data['description'] = category.description
            data['products-count'] = counts.get(category.id, 0)
            result.append(data)
        return 'SUCCESS', [], result
    except Exception:
        log.exception('%s - %s: site.categories error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products', methods=['GET'])
@api_response
def product_list():
    """?search=&category=<slug>&featured=1&page=&per-page="""
    log.debug('%s - %s: site.products', get_remote_ip(), request.method)

    try:
        search = (request.args.get('search') or '').strip()[:MAX_SEARCH_LENGTH] or None
        category_slug = (request.args.get('category') or '').strip() or None
        featured = request.args.get('featured') in ('1', 'true')
        page = _positive_int_arg('page', 1)
        per_page = min(_positive_int_arg('per-page', DEFAULT_PER_PAGE), MAX_PER_PAGE)

        products, total = product_access.list_public_page(search, category_slug, featured, page, per_page)
        return 'SUCCESS', [], {'items': _cards(products),
                               'total': total,
                               'page': page,
                               'per-page': per_page}
    except Exception:
        log.exception('%s - %s: site.products error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products/<slug>', methods=['GET'])
@api_response
def product_get(slug):
    log.debug('%s - %s: site.product %s', get_remote_ip(), request.method, slug)

    try:
        product = product_access.get_public_by_slug(slug)
        if product is None:
            return 'ERROR', ['product-not-found'], None

        images = product_access.images_of([product.id]).get(product.id, [])
        data = _card_json(product, images)
        data['description'] = product.description
        data['images'] = [media_json(i.media) for i in images]
        data['related'] = _cards(product_access.related(product, RELATED_LIMIT))
        return 'SUCCESS', [], data
    except Exception:
        log.exception('%s - %s: site.product error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
