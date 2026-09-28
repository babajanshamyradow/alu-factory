#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy.exc import IntegrityError

from backend.src.db import db
from backend.src.model import CompanyInfo
from backend.src.model.enums import AuditAction
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)

# tbl_company_info is a singleton: CHECK (id = 1).
COMPANY_ID = 1


def get():
    return CompanyInfo.query.get(COMPANY_ID)


def add(fields, action_username):
    """Create the single company row. Returns None if it already exists
    (including when a concurrent request created it first)."""
    if get() is not None:
        return None

    company = CompanyInfo(id=COMPANY_ID, **fields)
    db.session.add(company)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return None

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=CompanyInfo.__tablename__, record_id=str(COMPANY_ID),
                      description='Created company info %s' % company.company_name,
                      new_data=company.to_json())
    db.session.commit()
    return company


def edit(company, fields, action_username):
    snapshot = company.to_json()

    for key, value in fields.items():
        setattr(company, key, value)
    db.session.flush()

    _write_audit_log(action=AuditAction.update, username=action_username,
                      table_name=CompanyInfo.__tablename__, record_id=str(COMPANY_ID),
                      description='Edited company info %s' % company.company_name,
                      old_data=snapshot, new_data=company.to_json())
    db.session.commit()
    return company
