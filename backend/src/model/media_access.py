#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import logging
import os
import uuid

from datetime import datetime

from PIL import Image

from backend.src.db import db
from backend.src.model import Media, ProductImage, SliderItem, Banner, CompanyInfo, CompanyImage
from backend.src.model.enums import AuditAction, MediaType
from backend.src.model.user_access import _write_audit_log

log = logging.getLogger(__name__)

# extension -> (media type, mime type). SVG is deliberately absent: it can
# carry scripts and is served from our own origin.
ALLOWED_TYPES = {
    'jpg': (MediaType.image, 'image/jpeg'),
    'jpeg': (MediaType.image, 'image/jpeg'),
    'png': (MediaType.image, 'image/png'),
    'webp': (MediaType.image, 'image/webp'),
    'gif': (MediaType.image, 'image/gif'),
    'mp4': (MediaType.video, 'video/mp4'),
    'webm': (MediaType.video, 'video/webm'),
}


def get(media_id):
    return Media.query.get(media_id)


def media_type_for(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext, ALLOWED_TYPES.get(ext)


def save_upload(file_storage, upload_folder, alt_text, action_username):
    """Store an uploaded file on disk and register it in tbl_media.

    Returns the Media row, or None when the file claims to be an image but
    Pillow cannot read it.
    """
    ext, (media_type, mime_type) = media_type_for(file_storage.filename)

    now = datetime.utcnow()
    rel_path = '%04d/%02d/%s.%s' % (now.year, now.month, uuid.uuid4().hex, ext)
    abs_path = os.path.join(upload_folder, rel_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    file_storage.save(abs_path)

    width = height = None
    if media_type == MediaType.image:
        try:
            with Image.open(abs_path) as img:
                img.verify()
            with Image.open(abs_path) as img:
                width, height = img.size
        except Exception:
            os.remove(abs_path)
            return None

    media = Media(file_path=rel_path,
                  media_type=media_type,
                  alt_text=alt_text,
                  original_filename=file_storage.filename[:255],
                  mime_type=mime_type,
                  file_size_bytes=os.path.getsize(abs_path),
                  width=width,
                  height=height,
                  uploaded_by=action_username)
    db.session.add(media)
    db.session.flush()

    _write_audit_log(action=AuditAction.create, username=action_username,
                      table_name=Media.__tablename__, record_id=str(media.id),
                      description='Uploaded media %s' % media.original_filename)
    db.session.commit()
    return media


def is_used(media_id):
    refs = [
        ProductImage.query.filter(ProductImage.media_id == media_id),
        SliderItem.query.filter(SliderItem.media_id == media_id),
        Banner.query.filter(Banner.media_id == media_id),
        CompanyImage.query.filter(CompanyImage.media_id == media_id),
        CompanyInfo.query.filter(db.or_(CompanyInfo.logo_media_id == media_id,
                                        CompanyInfo.cover_media_id == media_id)),
    ]
    return any(db.session.query(q.exists()).scalar() for q in refs)


def delete_if_unused(media_id, upload_folder, action_username):
    """Drop a media row and its file once nothing references it any more.

    Call after the referencing row has been deleted or pointed elsewhere and
    committed. Failures are logged, never raised — a leftover file must not
    fail the user's actual action.
    """
    try:
        media = get(media_id)
        if media is None or is_used(media_id):
            return False

        rel_path = media.file_path
        db.session.delete(media)
        _write_audit_log(action=AuditAction.delete, username=action_username,
                          table_name=Media.__tablename__, record_id=str(media_id),
                          description='Deleted unused media %s' % rel_path,
                          old_data=media.to_json())
        db.session.commit()

        abs_path = os.path.join(upload_folder, rel_path)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        return True
    except Exception:
        db.session.rollback()
        log.exception('Failed to clean up media %s', media_id)
        return False
