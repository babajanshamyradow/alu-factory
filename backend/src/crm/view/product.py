#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request, g, current_app

from backend.src.crm.view import api_response, roles_required
from backend.src.crm.view.media import media_json
from backend.src.crm.view.validation import SLUG_RE, slugify, is_int, optional_str
from backend.src.util import get_remote_ip
from backend.src.model import product_access, category_access, media_access
from backend.src.model.enums import UserRole, MediaType


bp = Blueprint('product', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

LOOKUP_LIMIT = 20
MAX_NAME_LENGTH = 200
MAX_SLUG_LENGTH = 220
MAX_IMAGES = 20
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
STATUS_FILTERS = ('active', 'hidden', 'featured')


def product_brief(product):
    """Short product JSON for pickers and for entities that link a product."""
    if product is None:
        return None
    return {'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'short-description': product.short_description,
            'is-active': product.is_active}


def _image_json(image):
    return {'id': image.id,
            'media-id': image.media_id,
            'is-primary': image.is_primary,
            'sort-order': image.sort_order,
            'media': media_json(image.media)}


def _to_json(product, images, with_images):
    """`with_images`: the full list (edit form) or only the cover (table)."""
    data = product.to_json()
    category = product.category
    data['category'] = {'id': category.id, 'name': category.name} if category else None
    data['images-count'] = len(images)
    data['cover'] = media_json(images[0].media) if images else None
    if with_images:
        data['images'] = [_image_json(i) for i in images]
    return data


def _single_json(product):
    images = product_access.images_of([product.id]).get(product.id, [])
    return _to_json(product, images, with_images=True)


def _validate_images(value, error_msg):
    """[{'media-id', 'is-primary'}] in display order -> [(media_id, is_primary)].

    Exactly one image ends up primary: the one marked, or the first.
    """
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_IMAGES:
        error_msg.append('product-images-invalid')
        return []

    images, seen = [], set()
    for entry in value:
        media_id = entry.get('media-id') if isinstance(entry, dict) else None
        media = media_access.get(media_id) if is_int(media_id) else None
        if media is None or media.media_type != MediaType.image or media_id in seen:
            error_msg.append('product-images-invalid')
            return []
        seen.add(media_id)
        images.append((media_id, entry.get('is-primary') is True))

    primaries = [i for i, (_, primary) in enumerate(images) if primary]
    primary_index = primaries[0] if primaries else 0
    return [(media_id, i == primary_index) for i, (media_id, _) in enumerate(images)]


def _validate(data, error_msg, exclude_id=None):
    name = (data.get('name') or '').strip() if isinstance(data.get('name'), str) else ''
    if not name or len(name) > MAX_NAME_LENGTH:
        error_msg.append('product-name-invalid')

    slug = data.get('slug') if isinstance(data.get('slug'), str) else ''
    slug = slug.strip().lower() or slugify(name, MAX_SLUG_LENGTH)
    if not slug or len(slug) > MAX_SLUG_LENGTH or not SLUG_RE.match(slug):
        error_msg.append('product-slug-invalid')
    elif product_access.slug_exists(slug, exclude_id):
        error_msg.append('product-slug-exists')

    category_id = data.get('category-id')
    if not is_int(category_id) or category_access.get(category_id) is None:
        error_msg.append('product-category-invalid')

    short_description = optional_str(data, 'short-description', 500, 'product-short-description-invalid', error_msg)
    description = optional_str(data, 'description', 100000, 'product-description-invalid', error_msg)

    is_active = data.get('is-active', True)
    is_featured = data.get('is-featured', False)
    if not isinstance(is_active, bool) or not isinstance(is_featured, bool):
        error_msg.append('product-flags-invalid')
    sort_order = data.get('sort-order', 0)
    if not is_int(sort_order):
        error_msg.append('product-sort-order-invalid')

    return {'category_id': category_id,
            'name': name,
            'slug': slug,
            'short_description': short_description,
            'description': description,
            'is_active': is_active,
            'is_featured': is_featured,
            'sort_order': sort_order}


def _cleanup_media(media_ids):
    for media_id in media_ids:
        media_access.delete_if_unused(media_id, current_app.config['MEDIA_UPLOAD_FOLDER'], g.user.username)


def _positive_int_arg(name, default):
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


@bp.route('/products/lookup', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def product_lookup():
    log.debug('%s - %s - %s: product.lookup', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        return 'SUCCESS', [], [product_brief(p) for p in product_access.lookup(search, LOOKUP_LIMIT)]
    except Exception:
        log.exception('%s - %s: product.lookup error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def product_list():
    log.debug('%s - %s - %s: product.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        category_id = request.args.get('category-id', type=int)
        status = request.args.get('status')
        status = status if status in STATUS_FILTERS else None
        page = _positive_int_arg('page', 1)
        per_page = min(_positive_int_arg('per-page', DEFAULT_PER_PAGE), MAX_PER_PAGE)

        products, total = product_access.list_page(search, category_id, status, page, per_page)
        images = product_access.images_of([p.id for p in products])
        return 'SUCCESS', [], {'items': [_to_json(p, images.get(p.id, []), with_images=False) for p in products],
                               'total': total,
                               'page': page,
                               'per-page': per_page}
    except Exception:
        log.exception('%s - %s: product.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products/<int:product_id>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def product_get(product_id):
    log.debug('%s - %s - %s: product.get %s', get_remote_ip(), request.method, g.user.username, product_id)

    product = product_access.get(product_id)
    if product is None:
        return 'ERROR', ['product-not-found'], None
    return 'SUCCESS', [], _single_json(product)


@bp.route('/products', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def product_add():
    log.debug('%s - %s - %s: product.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        fields = _validate(data, error_msg)
        images = _validate_images(data.get('images'), error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        product = product_access.add(fields, images, g.user.username)
        return 'SUCCESS', [], _single_json(product)
    except Exception:
        log.exception('%s - %s: product.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products/<int:product_id>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def product_edit(product_id):
    """Full update. `version` is required (optimistic locking); `images`
    may be omitted to leave them unchanged (used by the table toggles)."""
    log.debug('%s - %s - %s: product.edit %s', get_remote_ip(), request.method, g.user.username, product_id)

    error_msg = []
    try:
        product = product_access.get(product_id)
        if product is None:
            return 'ERROR', ['product-not-found'], None

        data = request.get_json() or {}
        version = data.get('version')
        if not is_int(version):
            error_msg.append('product-version-invalid')
        fields = _validate(data, error_msg, exclude_id=product_id)
        images = _validate_images(data['images'], error_msg) if 'images' in data else None
        if error_msg:
            return 'ERROR', error_msg, None

        ok, detached = product_access.edit(product, version, fields, images, g.user.username)
        if not ok:
            return 'ERROR', ['product-modified'], None
        _cleanup_media(detached)
        return 'SUCCESS', [], _single_json(product_access.get(product_id))
    except Exception:
        log.exception('%s - %s: product.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/products/<int:product_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def product_delete(product_id):
    log.debug('%s - %s - %s: product.delete %s', get_remote_ip(), request.method, g.user.username, product_id)

    try:
        product = product_access.get(product_id)
        if product is None:
            return 'ERROR', ['product-not-found'], None

        # A banner advertising a vanished product would silently lose its
        # target — make the admin unlink or remove those banners first.
        if product_access.banner_count(product_id) > 0:
            return 'ERROR', ['product-used-in-banners'], None

        detached = product_access.delete(product, g.user.username)
        if detached is None:
            return 'ERROR', ['product-not-found'], None
        _cleanup_media(detached)
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: product.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
