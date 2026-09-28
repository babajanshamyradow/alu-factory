#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, func

from backend.src.db import db
from backend.src.model import Product, ProductImage, Banner, Category
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(product_id):
    return Product.query.get(product_id)


def _search_filter(q, search):
    return q.filter(or_(Product.name.ilike('%' + search + '%'),
                        Product.slug.ilike('%' + search + '%')))


def lookup(search=None, limit=20):
    """Lightweight product search for pickers (e.g. the banner form)."""
    q = Product.query
    if search:
        q = _search_filter(q, search)
    return q.order_by(Product.is_active.desc(), Product.name.asc()).limit(limit).all()


def list_page(search=None, category_id=None, status=None, page=1, per_page=20):
    """One page of products for the admin table: (products, total).

    `status`: None (all), 'active', 'hidden' or 'featured'.
    """
    q = Product.query
    if search:
        q = _search_filter(q, search)
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    if status == 'active':
        q = q.filter(Product.is_active.is_(True))
    elif status == 'hidden':
        q = q.filter(Product.is_active.is_(False))
    elif status == 'featured':
        q = q.filter(Product.is_featured.is_(True))

    total = q.order_by(None).count()
    products = q.order_by(Product.sort_order.asc(), Product.name.asc(), Product.id.asc()) \
        .offset((page - 1) * per_page).limit(per_page).all()
    return products, total


def _public_query():
    """Products visitors may see: active, in an active category."""
    return Product.query.join(Category, Product.category_id == Category.id) \
        .filter(Product.is_active.is_(True), Category.is_active.is_(True))


def _public_order(q):
    return q.order_by(Product.sort_order.asc(), Product.name.asc(), Product.id.asc())


def list_public_page(search=None, category_slug=None, featured=False, page=1, per_page=12):
    """One page of the public catalog: (products, total)."""
    q = _public_query()
    if search:
        q = q.filter(or_(Product.name.ilike('%' + search + '%'),
                         Product.short_description.ilike('%' + search + '%')))
    if category_slug:
        q = q.filter(Category.slug == category_slug)
    if featured:
        q = q.filter(Product.is_featured.is_(True))

    total = q.order_by(None).count()
    products = _public_order(q).offset((page - 1) * per_page).limit(per_page).all()
    return products, total


def get_public_by_slug(slug):
    return _public_query().filter(Product.slug == slug).first()


def related(product, limit=4):
    """Other visible products of the same category."""
    q = _public_query().filter(Product.category_id == product.category_id, Product.id != product.id)
    return _public_order(q).limit(limit).all()


def images_of(product_ids):
    """{product_id: [ProductImage, ...]} ordered for display, primary first."""
    if not product_ids:
        return {}
    rows = ProductImage.query.filter(ProductImage.product_id.in_(product_ids)) \
        .order_by(ProductImage.is_primary.desc(), ProductImage.sort_order.asc(), ProductImage.id.asc()).all()
    result = {}
    for row in rows:
        result.setdefault(row.product_id, []).append(row)
    return result


def slug_exists(slug, exclude_id=None):
    q = Product.query.filter(Product.slug == slug)
    if exclude_id is not None:
        q = q.filter(Product.id != exclude_id)
    return db.session.query(q.exists()).scalar()


def banner_count(product_id):
    return db.session.query(func.count(Banner.id)).filter(Banner.product_id == product_id).scalar()


def _snapshot(product):
    data = product.to_json()
    data['images'] = [{'media-id': i.media_id, 'is-primary': i.is_primary}
                      for i in images_of([product.id]).get(product.id, [])]
    return data


def _replace_images(product_id, images):
    """Make the product's images exactly `images` [(media_id, is_primary)],
    in that order. Returns media ids that are no longer attached."""
    old_ids = {i.media_id for i in ProductImage.query.filter(ProductImage.product_id == product_id)}
    ProductImage.query.filter(ProductImage.product_id == product_id).delete(synchronize_session=False)
    db.session.flush()
    for index, (media_id, is_primary) in enumerate(images):
        db.session.add(ProductImage(product_id=product_id, media_id=media_id,
                                    is_primary=is_primary, sort_order=index))
    return old_ids - {media_id for media_id, _ in images}


def add(fields, images, action_username):
    product = Product(version=0, **fields)
    db.session.add(product)
    db.session.flush()
    _replace_images(product.id, images)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=Product.__tablename__, record_id=str(product.id),
                      description='Created product %s' % product.name,
                      new_data=_snapshot(product))
    db.session.commit()
    return product


def edit(product, version, fields, images, action_username):
    """Optimistic-locked update. `images` None leaves the images untouched.

    Returns (ok, detached media ids); ok is False when `version` is stale.
    """
    snapshot = _snapshot(product)

    changes = {getattr(Product, key): value for key, value in fields.items()}
    changes[Product.version] = version + 1
    q = Product.query.filter(Product.id == product.id, Product.version == version)
    if q.update(changes, synchronize_session=False) == 0:
        db.session.rollback()
        return False, set()

    detached = _replace_images(product.id, images) if images is not None else set()
    db.session.flush()
    db.session.expire(product)

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=Product.__tablename__, record_id=str(product.id),
                      description='Edited product %s' % fields['name'],
                      old_data=snapshot, new_data=_snapshot(product))
    db.session.commit()
    return True, detached


def delete(product, action_username):
    """Delete the product and its image links. Returns the detached media
    ids, or None when the product was already gone."""
    product_id = product.id
    snapshot = _snapshot(product)
    detached = {i['media-id'] for i in snapshot['images']}

    ProductImage.query.filter(ProductImage.product_id == product_id).delete(synchronize_session=False)
    if Product.query.filter(Product.id == product_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return None

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=Product.__tablename__, record_id=str(product_id),
                      description='Deleted product %s' % snapshot['name'],
                      old_data=snapshot)
    db.session.commit()
    return detached
