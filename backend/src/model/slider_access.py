#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, and_

from backend.src.db import db
from backend.src.model import SliderItem
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(item_id):
    return SliderItem.query.get(item_id)


def list_all(search=None):
    q = SliderItem.query
    if search:
        q = q.filter(or_(SliderItem.title.ilike('%' + search + '%'),
                          SliderItem.subtitle.ilike('%' + search + '%')))
    return q.order_by(SliderItem.sort_order.asc(), SliderItem.id.asc()).all()


def _in_window(model, now):
    """Active items whose optional [starts_at, ends_at] window contains `now`."""
    return and_(model.is_active.is_(True),
                or_(model.starts_at.is_(None), model.starts_at <= now),
                or_(model.ends_at.is_(None), model.ends_at >= now))


def list_public(now):
    """What the public site shows right now, in display order."""
    return SliderItem.query.filter(_in_window(SliderItem, now)) \
        .order_by(SliderItem.sort_order.asc(), SliderItem.id.asc()).all()


def add(fields, action_username):
    item = SliderItem(**fields)
    db.session.add(item)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=SliderItem.__tablename__, record_id=str(item.id),
                      description='Created slider item %s' % (item.title or item.id),
                      new_data=item.to_json())
    db.session.commit()
    return item


def edit(item, fields, action_username):
    snapshot = item.to_json()

    for key, value in fields.items():
        setattr(item, key, value)
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=SliderItem.__tablename__, record_id=str(item.id),
                      description='Edited slider item %s' % (item.title or item.id),
                      old_data=snapshot, new_data=item.to_json())
    db.session.commit()
    return item


def delete(item, action_username):
    item_id = item.id
    snapshot = item.to_json()

    if SliderItem.query.filter(SliderItem.id == item_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=SliderItem.__tablename__, record_id=str(item_id),
                      description='Deleted slider item %s' % (snapshot['title'] or item_id),
                      old_data=snapshot)
    db.session.commit()
    return True
