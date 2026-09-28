#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, and_

from backend.src.db import db
from backend.src.model import Banner
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(banner_id):
    return Banner.query.get(banner_id)


def list_all(search=None):
    q = Banner.query
    if search:
        q = q.filter(or_(Banner.title.ilike('%' + search + '%'),
                          Banner.subtitle.ilike('%' + search + '%')))
    return q.order_by(Banner.sort_order.asc(), Banner.id.asc()).all()


def _in_window(model, now):
    """Active items whose optional [starts_at, ends_at] window contains `now`."""
    return and_(model.is_active.is_(True),
                or_(model.starts_at.is_(None), model.starts_at <= now),
                or_(model.ends_at.is_(None), model.ends_at >= now))


def list_public(now):
    """What the public site shows right now, in display order."""
    return Banner.query.filter(_in_window(Banner, now)) \
        .order_by(Banner.sort_order.asc(), Banner.id.asc()).all()


def add(fields, action_username):
    banner = Banner(**fields)
    db.session.add(banner)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=Banner.__tablename__, record_id=str(banner.id),
                      description='Created banner %s' % (banner.title or banner.id),
                      new_data=banner.to_json())
    db.session.commit()
    return banner


def edit(banner, fields, action_username):
    snapshot = banner.to_json()

    for key, value in fields.items():
        setattr(banner, key, value)
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=Banner.__tablename__, record_id=str(banner.id),
                      description='Edited banner %s' % (banner.title or banner.id),
                      old_data=snapshot, new_data=banner.to_json())
    db.session.commit()
    return banner


def delete(banner, action_username):
    banner_id = banner.id
    snapshot = banner.to_json()

    if Banner.query.filter(Banner.id == banner_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=Banner.__tablename__, record_id=str(banner_id),
                      description='Deleted banner %s' % (snapshot['title'] or banner_id),
                      old_data=snapshot)
    db.session.commit()
    return True
