#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from flask import Blueprint, request, g

from backend.src.crm.view import api_response, roles_required
from backend.src.crm.view.validation import SLUG_RE, slugify
from backend.src.util import get_remote_ip
from backend.src.model import category_access
from backend.src.model.enums import UserRole


bp = Blueprint('category', __name__, url_prefix='/api')
log = logging.getLogger(__name__)

MAX_NAME_LENGTH = 128
MAX_SLUG_LENGTH = 160


def _to_json(category, products_count=0):
    data = category.to_json()
    data['products-count'] = products_count
    return data


def _validate(data, error_msg, exclude_id=None):
    name = (data.get('name') or '').strip()
    slug = (data.get('slug') or '').strip().lower() or slugify(name, MAX_SLUG_LENGTH)
    description = (data.get('description') or '').strip() or None
    is_active = data.get('is-active', True)
    sort_order = data.get('sort-order', 0)

    if not name or len(name) > MAX_NAME_LENGTH:
        error_msg.append('category-name-invalid')
    elif category_access.name_exists(name, exclude_id):
        error_msg.append('category-name-exists')

    if not slug or len(slug) > MAX_SLUG_LENGTH or not SLUG_RE.match(slug):
        error_msg.append('category-slug-invalid')
    elif category_access.slug_exists(slug, exclude_id):
        error_msg.append('category-slug-exists')

    if not isinstance(is_active, bool):
        error_msg.append('category-is-active-invalid')
    # bool is a subclass of int — reject it explicitly.
    if not isinstance(sort_order, int) or isinstance(sort_order, bool):
        error_msg.append('category-sort-order-invalid')

    return name, slug, description, is_active, sort_order


@bp.route('/categories', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def category_list():
    log.debug('%s - %s - %s: category.list', get_remote_ip(), request.method, g.user.username)

    try:
        search = (request.args.get('search') or '').strip() or None
        categories = category_access.list_all(search)
        counts = category_access.product_counts([c.id for c in categories])
        return 'SUCCESS', [], [_to_json(c, counts.get(c.id, 0)) for c in categories]
    except Exception:
        log.exception('%s - %s: category.list error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/categories/<int:category_id>', methods=['GET'])
@roles_required(UserRole.superuser, UserRole.admin, UserRole.operator)
@api_response
def category_get(category_id):
    log.debug('%s - %s - %s: category.get %s', get_remote_ip(), request.method, g.user.username, category_id)

    category = category_access.get(category_id)
    if category is None:
        return 'ERROR', ['category-not-found'], None
    counts = category_access.product_counts([category.id])
    return 'SUCCESS', [], _to_json(category, counts.get(category.id, 0))


@bp.route('/categories', methods=['POST'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def category_add():
    log.debug('%s - %s - %s: category.add', get_remote_ip(), request.method, g.user.username)

    error_msg = []
    try:
        data = request.get_json() or {}
        name, slug, description, is_active, sort_order = _validate(data, error_msg)
        if error_msg:
            return 'ERROR', error_msg, None

        category = category_access.add(name, slug, description, is_active, sort_order, g.user.username)
        return 'SUCCESS', [], _to_json(category)
    except Exception:
        log.exception('%s - %s: category.add error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/categories/<int:category_id>', methods=['PUT'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def category_edit(category_id):
    log.debug('%s - %s - %s: category.edit %s', get_remote_ip(), request.method, g.user.username, category_id)

    error_msg = []
    try:
        category = category_access.get(category_id)
        if category is None:
            return 'ERROR', ['category-not-found'], None

        data = request.get_json() or {}
        name, slug, description, is_active, sort_order = _validate(data, error_msg, exclude_id=category_id)
        if error_msg:
            return 'ERROR', error_msg, None

        category = category_access.edit(category, name, slug, description, is_active, sort_order,
                                        g.user.username)
        counts = category_access.product_counts([category.id])
        return 'SUCCESS', [], _to_json(category, counts.get(category.id, 0))
    except Exception:
        log.exception('%s - %s: category.edit error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None


@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@roles_required(UserRole.superuser, UserRole.admin)
@api_response
def category_delete(category_id):
    log.debug('%s - %s - %s: category.delete %s', get_remote_ip(), request.method, g.user.username, category_id)

    try:
        category = category_access.get(category_id)
        if category is None:
            return 'ERROR', ['category-not-found'], None

        # tbl_product.category_id is NOT NULL — products must be moved or
        # deleted first, never silently cascaded.
        if category_access.product_counts([category.id]).get(category.id, 0) > 0:
            return 'ERROR', ['category-has-products'], None

        if not category_access.delete(category, g.user.username):
            return 'ERROR', ['category-not-found'], None
        return 'SUCCESS', [], None
    except Exception:
        log.exception('%s - %s: category.delete error', get_remote_ip(), request.method)
        return 'ERROR', ['internal-server-error'], None
