#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import base64

from datetime import datetime, timedelta
from passlib.hash import sha256_crypt
from sqlalchemy.dialects.postgresql import UUID, JSONB

from backend.src.db import db
from backend.src.model.enums import SystemLang, UserRole, MediaType, ContactStatus, AuditAction

SYS_PWD = '$5$rounds=921532132919358$SYSTEM$SYSTEM' \
          'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

class User(db.Model):
    __tablename__ = 'tbl_user'
    username = db.Column(db.String(64), primary_key=True)
    fullname = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    locked = db.Column(db.Boolean(), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    lang = db.Column(db.Enum(SystemLang), nullable=False, default='en')
    email = db.Column(db.String(256), nullable=True)

    access_token = db.Column(db.String(32), index=True, unique=True)
    access_token_expiration = db.Column(db.DateTime(timezone=False), nullable=True)
    refresh_token = db.Column(db.String(32), index=True, unique=True)    
    firebase_token = db.Column(db.Text(), nullable=True)
    
    version = db.Column(db.Integer(), nullable=False)
    
    def to_json(self):
        return {'username': self.username,
                'fullname': self.fullname,
                'locked': self.locked,
                'role': self.role.value,
                'lang': self.lang.value,
                'email': self.email,
                'version': self.version}
    
    def get_api_token(self, expires_in=172800):
        now = datetime.utcnow()

        if self.access_token and self.access_token_expiration is not None and self.access_token_expiration > now + timedelta(seconds=60):
            return self.access_token, self.refresh_token, expires_in

        self.access_token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.access_token_expiration = now + timedelta(seconds=expires_in)
        self.refresh_token = base64.b64encode(os.urandom(24)).decode('utf-8')

        db.session.add(self)
        db.session.commit()
        return self.access_token, self.refresh_token, expires_in

    def revoke_api_token(self):
        self.access_token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_access_token(access_token):
        user = User.query.filter(User.access_token == access_token).first()
        if user is None or user.access_token_expiration < datetime.utcnow():
            return None
        return user

    @staticmethod
    def get_user_from_access_token(access_token):
        user = User.query.filter(User.access_token == access_token).first()
        return user

    @staticmethod
    def get_user_from_refresh_token(refresh_token):
        user = User.query.filter(User.refresh_token == refresh_token).first()
        return user


class UserLoginLog(db.Model):
    __tablename__ = 'tbl_user_login_log'
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    username = db.Column(db.String(64),
                         db.ForeignKey(User.__tablename__ + '.username'),
                         nullable=False)
    action_ts = db.Column(db.DateTime(timezone=False), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    additional_info = db.Column(db.String(64))

    def to_json(self):
        return {'status': self.status,
                'action-ts': self.action_ts.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                'additional-info': self.additional_info}


class UserLog(db.Model):
    __tablename__ = 'tbl_user_log'
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    username = db.Column(db.String(64),
                         db.ForeignKey(User.__tablename__ + '.username'),
                         nullable=False)
    action = db.Column(db.String(32), nullable=False)
    action_ts = db.Column(db.DateTime(timezone=False), nullable=False)
    action_user = db.Column(db.String(64),
                            db.ForeignKey(User.__tablename__ + '.username'),
                            nullable=False)
    version = db.Column(db.Integer(), nullable=False)
    reason = db.Column(db.String(128), nullable=False)
    additional_info = db.Column(db.String(32), nullable=False)

    def to_json(self):
        return {'action': self.action,
                'action-ts': self.action_ts.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                'action-user': self.action_user,
                'version': self.version,
                'reason': self.reason,
                'additional-info': self.additional_info}


## ---------------------------------------------------------------------------
## alu-factory site models (products/media/slider/banners/contact/about-us/log)
## Admin/staff accounts reuse the existing `User` (tbl_user) above rather than
## a separate table — its `role`/`email` columns already cover what the admin
## panel needs, so `Media.uploaded_by`/`AuditLog.username` FK to `tbl_user.username`.
## ---------------------------------------------------------------------------

class Media(db.Model):
    __tablename__ = 'tbl_media'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.Enum(MediaType), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)

    uploaded_by = db.Column(db.String(64), db.ForeignKey('tbl_user.username'), nullable=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)

    def to_json(self):
        return {'id': self.id,
                'file-path': self.file_path,
                'media-type': self.media_type.value,
                'alt-text': self.alt_text,
                'mime-type': self.mime_type,
                'width': self.width,
                'height': self.height,
                'created-at': self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z')}


class Category(db.Model):
    __tablename__ = 'tbl_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    slug = db.Column(db.String(160), nullable=False, unique=True)
    description = db.Column(db.Text(), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_json(self):
        return {'id': self.id,
                'name': self.name,
                'slug': self.slug,
                'description': self.description,
                'is-active': self.is_active,
                'sort-order': self.sort_order}


class Product(db.Model):
    __tablename__ = 'tbl_product'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('tbl_category.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True)
    short_description = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text(), nullable=True)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    is_featured = db.Column(db.Boolean(), nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, nullable=False, default=0)

    images = db.relationship('ProductImage', backref='product', lazy='dynamic',
                              order_by='ProductImage.sort_order')

    def to_json(self):
        return {'id': self.id,
                'category-id': self.category_id,
                'name': self.name,
                'slug': self.slug,
                'short-description': self.short_description,
                'description': self.description,
                'is-active': self.is_active,
                'is-featured': self.is_featured,
                'sort-order': self.sort_order,
                'version': self.version}


class ProductImage(db.Model):
    __tablename__ = 'tbl_product_image'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('tbl_product.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=False)
    is_primary = db.Column(db.Boolean(), nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)

    media = db.relationship('Media')

    __table_args__ = (
        db.UniqueConstraint('product_id', 'media_id', name='uq_product_image_product_media'),
    )

    def to_json(self):
        return {'id': self.id,
                'product-id': self.product_id,
                'media-id': self.media_id,
                'is-primary': self.is_primary,
                'sort-order': self.sort_order}


class SliderItem(db.Model):
    __tablename__ = 'tbl_slider_item'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    subtitle = db.Column(db.String(300), nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    starts_at = db.Column(db.DateTime(timezone=False), nullable=True)
    ends_at = db.Column(db.DateTime(timezone=False), nullable=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = db.relationship('Media')

    def to_json(self):
        return {'id': self.id,
                'media-id': self.media_id,
                'title': self.title,
                'subtitle': self.subtitle,
                'link-url': self.link_url,
                'sort-order': self.sort_order,
                'is-active': self.is_active,
                'starts-at': self.starts_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z') if self.starts_at else None,
                'ends-at': self.ends_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z') if self.ends_at else None}


class Banner(db.Model):
    __tablename__ = 'tbl_banner'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('tbl_product.id'), nullable=True)
    title = db.Column(db.String(200), nullable=True)
    subtitle = db.Column(db.String(300), nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    starts_at = db.Column(db.DateTime(timezone=False), nullable=True)
    ends_at = db.Column(db.DateTime(timezone=False), nullable=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = db.relationship('Media')
    product = db.relationship('Product')

    def to_json(self):
        return {'id': self.id,
                'media-id': self.media_id,
                'product-id': self.product_id,
                'title': self.title,
                'subtitle': self.subtitle,
                'link-url': self.link_url,
                'sort-order': self.sort_order,
                'is-active': self.is_active,
                'starts-at': self.starts_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z') if self.starts_at else None,
                'ends-at': self.ends_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z') if self.ends_at else None}


class ContactMessage(db.Model):
    __tablename__ = 'tbl_contact_message'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text(), nullable=False)
    status = db.Column(db.Enum(ContactStatus), nullable=False, default=ContactStatus.new)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.CheckConstraint('email IS NOT NULL OR phone IS NOT NULL', name='ck_contact_message_email_or_phone'),
    )

    def to_json(self):
        return {'id': self.id,
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'message': self.message,
                'status': self.status.value,
                'created-at': self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z')}


class CompanyInfo(db.Model):
    __tablename__ = 'tbl_company_info'
    id = db.Column(db.Integer, primary_key=True, default=1)
    company_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text(), nullable=True)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)
    description = db.Column(db.Text(), nullable=True)

    logo_media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=True)
    cover_media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=True)

    updated_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('id = 1', name='ck_company_info_singleton'),
    )

    logo_media = db.relationship('Media', foreign_keys=[logo_media_id])
    cover_media = db.relationship('Media', foreign_keys=[cover_media_id])

    def to_json(self):
        return {'company-name': self.company_name,
                'email': self.email,
                'phone': self.phone,
                'address': self.address,
                'latitude': float(self.latitude) if self.latitude is not None else None,
                'longitude': float(self.longitude) if self.longitude is not None else None,
                'description': self.description,
                'logo-media-id': self.logo_media_id,
                'cover-media-id': self.cover_media_id}


class CompanyImage(db.Model):
    __tablename__ = 'tbl_company_image'
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('tbl_media.id'), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow)

    media = db.relationship('Media')

    def to_json(self):
        return {'id': self.id,
                'media-id': self.media_id,
                'caption': self.caption,
                'sort-order': self.sort_order,
                'is-active': self.is_active}


class AuditLog(db.Model):
    __tablename__ = 'tbl_audit_log'
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(64), db.ForeignKey('tbl_user.username'), nullable=True)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    table_name = db.Column(db.String(64), nullable=True)
    record_id = db.Column(db.String(64), nullable=True)
    old_data = db.Column(JSONB, nullable=True)
    new_data = db.Column(JSONB, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime(timezone=False), nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('ix_audit_log_table_record', 'table_name', 'record_id'),
    )

    user = db.relationship('User')

    def to_json(self):
        return {'id': self.id,
                'username': self.username,
                'action': self.action.value,
                'table-name': self.table_name,
                'record-id': self.record_id,
                'old-data': self.old_data,
                'new-data': self.new_data,
                'description': self.description,
                'created-at': self.created_at.strftime('%Y-%m-%dT%H:%M:%S.%f%z')}


def remove_db():
    db.drop_all()
    db.session.commit()


def init_db():
    db.drop_all()
    db.session.commit()
    db.create_all()
    db.session.commit()


def fill_default():
    h1 = sha256_crypt.encrypt('12345')

    sys_user = User(username='SYSTEM',
                    fullname='System',
                    password=SYS_PWD,
                    locked=False,
                    role=UserRole.superuser,
                    lang=SystemLang.en,
                    version=0)

    su = User(username='superuser',
              fullname='Superuser',
              password=h1,
              locked=False,
              role=UserRole.superuser,
              lang=SystemLang.en,
              version=0)

    lms = User(username='admin',
               fullname='Admin',
               password=h1,
               locked=False,
               role=UserRole.admin,
               lang=SystemLang.en,
               version=0)

    db.session.add(sys_user)
    db.session.add(su)
    db.session.add(lms)
    db.session.commit()

def fill_temp():
    pass
