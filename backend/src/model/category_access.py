#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, func

from backend.src.db import db
from backend.src.model import Category, Product
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(category_id):
    return Category.query.get(category_id)


def list_all(search=None):
    q = Category.query
    if search:
        q = q.filter(or_(Category.name.ilike('%' + search + '%'),
                          Category.slug.ilike('%' + search + '%')))
    return q.order_by(Category.sort_order.asc(), Category.name.asc()).all()


def product_counts(category_ids):
    if not category_ids:
        return {}
    rows = db.session.query(Product.category_id, func.count(Product.id)) \
        .filter(Product.category_id.in_(category_ids)) \
        .group_by(Product.category_id).all()
    return dict(rows)


def list_public():
    """Active categories for the public site."""
    return Category.query.filter(Category.is_active.is_(True)) \
        .order_by(Category.sort_order.asc(), Category.name.asc()).all()


def active_product_counts(category_ids):
    """{category_id: number of active products} — what the public site shows."""
    if not category_ids:
        return {}
    rows = db.session.query(Product.category_id, func.count(Product.id)) \
        .filter(Product.category_id.in_(category_ids), Product.is_active.is_(True)) \
        .group_by(Product.category_id).all()
    return dict(rows)


def name_exists(name, exclude_id=None):
    q = Category.query.filter(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        q = q.filter(Category.id != exclude_id)
    return db.session.query(q.exists()).scalar()


def slug_exists(slug, exclude_id=None):
    q = Category.query.filter(Category.slug == slug)
    if exclude_id is not None:
        q = q.filter(Category.id != exclude_id)
    return db.session.query(q.exists()).scalar()


def add(name, slug, description, is_active, sort_order, action_username):
    category = Category(name=name,
                        slug=slug,
                        description=description,
                        is_active=is_active,
                        sort_order=sort_order)
    db.session.add(category)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=Category.__tablename__, record_id=str(category.id),
                      description='Created category %s' % name,
                      new_data=category.to_json())
    db.session.commit()
    return category


def edit(category, name, slug, description, is_active, sort_order, action_username):
    snapshot = category.to_json()

    category.name = name
    category.slug = slug
    category.description = description
    category.is_active = is_active
    category.sort_order = sort_order
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=Category.__tablename__, record_id=str(category.id),
                      description='Edited category %s' % name,
                      old_data=snapshot, new_data=category.to_json())
    db.session.commit()
    return category


def delete(category, action_username):
    category_id = category.id
    snapshot = category.to_json()

    if Category.query.filter(Category.id == category_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=Category.__tablename__, record_id=str(category_id),
                      description='Deleted category %s' % snapshot['name'],
                      old_data=snapshot)
    db.session.commit()
    return True
