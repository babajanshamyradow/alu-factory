#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import or_, func

from backend.src.db import db
from backend.src.model import ContactMessage
from backend.src.model.enums import AuditAction, ContactStatus
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)


def get(message_id):
    return ContactMessage.query.get(message_id)


def list_page(search=None, status=None, page=1, per_page=20):
    """One page of messages, newest first: (messages, total)."""
    q = ContactMessage.query
    if search:
        pattern = '%' + search + '%'
        q = q.filter(or_(ContactMessage.name.ilike(pattern),
                          ContactMessage.email.ilike(pattern),
                          ContactMessage.phone.ilike(pattern),
                          ContactMessage.message.ilike(pattern)))
    if status is not None:
        q = q.filter(ContactMessage.status == status)

    total = q.order_by(None).count()
    messages = q.order_by(ContactMessage.created_at.desc(), ContactMessage.id.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()
    return messages, total


def status_counts():
    """{'new': n, 'read': n, 'archived': n} — every status present, 0 if none."""
    rows = db.session.query(ContactMessage.status, func.count(ContactMessage.id)) \
        .group_by(ContactMessage.status).all()
    counts = {s.value: 0 for s in ContactStatus}
    counts.update({status.value: count for status, count in rows})
    return counts


def submit(fields, ip_address, user_agent):
    """Store a message from the public contact form (no logged-in user)."""
    message = ContactMessage(status=ContactStatus.new,
                             ip_address=ip_address,
                             user_agent=(user_agent or '')[:255] or None,
                             **fields)
    db.session.add(message)
    db.session.flush()

    _write_audit_log(action=AuditAction.contact_submitted, username=None,
                      table_name=ContactMessage.__tablename__, record_id=str(message.id),
                      description='Contact form submitted by %s' % message.name[:100],
                      ip_address=ip_address, user_agent=message.user_agent)
    db.session.commit()
    return message


def set_status(message, status, action_username):
    old_status = message.status
    if old_status == status:
        return message

    message.status = status
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=ContactMessage.__tablename__, record_id=str(message.id),
                      description='Contact message status %s -> %s' % (old_status.value, status.value),
                      old_data={'status': old_status.value}, new_data={'status': status.value})
    db.session.commit()
    return message


def delete(message, action_username):
    message_id = message.id
    snapshot = message.to_json()

    if ContactMessage.query.filter(ContactMessage.id == message_id).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=ContactMessage.__tablename__, record_id=str(message_id),
                      description='Deleted contact message from %s' % snapshot['name'][:100],
                      old_data=snapshot)
    db.session.commit()
    return True
