#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import func

from backend.src.db import db
from backend.src.model import CompanyImage
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(image_id):
    return CompanyImage.query.get(image_id)


def list_all():
    return CompanyImage.query.order_by(CompanyImage.sort_order.asc(), CompanyImage.id.asc()).all()


def list_active():
    return CompanyImage.query.filter(CompanyImage.is_active.is_(True)) \
        .order_by(CompanyImage.sort_order.asc(), CompanyImage.id.asc()).all()


def next_sort_order():
    current = db.session.query(func.max(CompanyImage.sort_order)).scalar()
    return 0 if current is None else current + 1


def add(fields, action_username):
    image = CompanyImage(**fields)
    db.session.add(image)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=CompanyImage.__tablename__, record_id=str(image.id),
                      description='Added company gallery image',
                      new_data=image.to_json())
    db.session.commit()
    return image


def edit(image, fields, action_username):
    snapshot = image.to_json()

    for key, value in fields.items():
        setattr(image, key, value)
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=CompanyImage.__tablename__, record_id=str(image.id),
                      description='Edited company gallery image',
                      old_data=snapshot, new_data=image.to_json())
    db.session.commit()
    return image


def reorder(ids, action_username):
    """Set sort_order to each id's position. `ids` must be exactly the
    current set of images; returns False otherwise (someone added/removed
    one meanwhile)."""
    images = {i.id: i for i in CompanyImage.query.all()}
    if len(ids) != len(images) or set(ids) != set(images):
        return False

    old_order = [i.id for i in sorted(images.values(), key=lambda i: (i.sort_order, i.id))]
    for index, image_id in enumerate(ids):
        images[image_id].sort_order = index
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=CompanyImage.__tablename__,
                      description='Reordered company gallery',
                      old_data={'order': old_order}, new_data={'order': ids})
    db.session.commit()
    return True


def delete(image, action_username):
    image_id = image.id
    snapshot = image.to_json()

    if CompanyImage.query.filter(CompanyImage.id == image_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=CompanyImage.__tablename__, record_id=str(image_id),
                      description='Deleted company gallery image',
                      old_data=snapshot)
    db.session.commit()
    return True
