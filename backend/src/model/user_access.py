#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging
import datetime

from sqlalchemy import or_
from passlib.hash import sha256_crypt

from backend.src.db import db
from backend.src.model import User, AuditLog, Media, UserLog, UserLoginLog
from backend.src.model.enums import AuditAction

log = logging.getLogger(__name__)


def get_user(username):
    return User.query.get(username)


def list_all(search=None):
    q = User.query.filter(User.username != 'SYSTEM')
    if search:
        q = q.filter(or_(User.username.ilike('%' + search + '%'),
                          User.fullname.ilike('%' + search + '%'),
                          User.email.ilike('%' + search + '%')))
    return q.order_by(User.username.asc()).all()


def add(username, fullname, password, role, email, action_username):
    if User.query.get(username) is not None:
        return None

    user = User(username=username,
                fullname=fullname,
                password=sha256_crypt.encrypt(password),
                locked=False,
                role=role,
                lang='en',
                email=email,
                version=0)
    db.session.add(user)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=User.__tablename__, record_id=username,
                      description='Created admin user %s' % username)

    db.session.commit()
    return user


def edit(user, fullname, email, role, action_username):
    user_cv = user.version
    changes = {
        User.fullname: fullname,
        User.email: email,
        User.role: role,
        User.version: user_cv + 1,
    }

    q = User.query.filter(User.username == user.username, User.version == user_cv)
    if q.update(changes) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=User.__tablename__, record_id=user.username,
                      description='Edited admin user %s' % user.username)
    db.session.commit()
    return True


def set_locked(user, locked, action_username):
    user_cv = user.version
    changes = {User.locked: locked, User.version: user_cv + 1}

    q = User.query.filter(User.username == user.username, User.version == user_cv)
    if q.update(changes) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=User.__tablename__, record_id=user.username,
                      description='%s admin user %s' % ('Locked' if locked else 'Unlocked', user.username))
    db.session.commit()
    return True


def change_password(user, password, action_username):
    user_cv = user.version
    changes = {User.password: sha256_crypt.encrypt(password), User.version: user_cv + 1}

    q = User.query.filter(User.username == user.username, User.version == user_cv)
    if q.update(changes) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=User.__tablename__, record_id=user.username,
                      description='Changed password for admin user %s' % user.username)
    db.session.commit()
    return True


def delete(user, action_username):
    username = user.username
    snapshot = user.to_json()

    # Keep the audit trail and uploaded media, just detach them from the
    # deleted account (both FKs are nullable). The legacy log tables are not
    # used by the new code, so their rows for this user are simply dropped.
    AuditLog.query.filter(AuditLog.username == username) \
        .update({AuditLog.username: None}, synchronize_session=False)
    Media.query.filter(Media.uploaded_by == username) \
        .update({Media.uploaded_by: None}, synchronize_session=False)
    UserLoginLog.query.filter(UserLoginLog.username == username) \
        .delete(synchronize_session=False)
    UserLog.query.filter(or_(UserLog.username == username, UserLog.action_user == username)) \
        .delete(synchronize_session=False)

    if User.query.filter(User.username == username).delete(synchronize_session=False) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.delete, username=action_username,
                      table_name=User.__tablename__, record_id=username,
                      description='Deleted admin user %s' % username,
                      old_data=snapshot)
    db.session.commit()
    return True


def verify_password(user_password_hash, password):
    return sha256_crypt.verify(password, user_password_hash)


def login(username, password, ip_address=None, user_agent=None):
    user = User.query.filter(User.username == username).first()

    if user is None:
        log.debug('Unknown user [%s] tried to login', username)
        _write_audit_log(action=AuditAction.login_failed, username=None,
                          description='Unknown username: %s' % username,
                          ip_address=ip_address, user_agent=user_agent)
        db.session.commit()
        return None

    if user.locked:
        log.debug('Locked user [%s] tried to login', username)
        _write_audit_log(action=AuditAction.login_failed, username=user.username,
                          description='Locked user attempted login',
                          ip_address=ip_address, user_agent=user_agent)
        db.session.commit()
        return None

    if not verify_password(user.password, password):
        log.debug('Wrong password for user [%s]', username)
        _write_audit_log(action=AuditAction.login_failed, username=user.username,
                          description='Wrong password',
                          ip_address=ip_address, user_agent=user_agent)
        db.session.commit()
        return None

    _write_audit_log(action=AuditAction.login, username=user.username,
                      description='Login success',
                      ip_address=ip_address, user_agent=user_agent)
    db.session.commit()
    return user


def logout(username, ip_address=None, user_agent=None):
    q = User.query.filter(User.username == username)
    if q.update({User.access_token: None, User.refresh_token: None, User.firebase_token: None}) == 0:
        db.session.rollback()
        return False

    _write_audit_log(action=AuditAction.logout, username=username,
                      description='Logout', ip_address=ip_address, user_agent=user_agent)
    db.session.commit()
    return True


def _write_audit_log(action, username=None, table_name=None, record_id=None,
                      description=None, ip_address=None, user_agent=None,
                      old_data=None, new_data=None):
    log_rec = AuditLog(username=username,
                       action=action,
                       table_name=table_name,
                       record_id=record_id,
                       old_data=old_data,
                       new_data=new_data,
                       description=description,
                       ip_address=ip_address,
                       user_agent=user_agent,
                       created_at=datetime.datetime.utcnow())
    db.session.add(log_rec)
