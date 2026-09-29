#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Request-field validators shared by the admin views."""

import re
import unicodedata

from datetime import datetime, timezone

from backend.src.model import media_access

# Absolute http(s) URL or a site-relative path like /products/doors.
LINK_URL_RE = re.compile(r'^(https?://[^\s]+|/[^\s]*)$')
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

# Letters NFKD can't fold to ASCII: Cyrillic (ru names) plus Turkish ı
# and German ß. Everything else with diacritics (ş, ň, ý, ä, ü...) is folded
# by NFKD below.
_TRANSLIT = dict(zip(
    'абвгдеёжзийклмнопрстуфхцчшщъыьэюяҗңөүәı',
    ['a', 'b', 'v', 'g', 'd', 'e', 'yo', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p',
     'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch', 'sh', 'shch', '', 'y', '', 'e', 'yu', 'ya',
     'j', 'n', 'o', 'u', 'a', 'i'],
))
_TRANSLIT['ß'] = 'ss'


def slugify(value, max_len):
    value = ''.join(_TRANSLIT.get(ch, ch) for ch in value.lower())
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return value[:max_len].strip('-')


def is_int(value):
    # bool is a subclass of int — reject it explicitly.
    return isinstance(value, int) and not isinstance(value, bool)


def parse_datetime(value):
    """ISO-8601 string -> naive UTC datetime (how the DB stores it).

    Returns (datetime or None, ok). A string without an offset is taken as
    UTC already.
    """
    if value is None or value == '':
        return None, True
    if not isinstance(value, str):
        return None, False
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None, False
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt, True


def optional_str(data, key, max_len, error_code, error_msg):
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or len(value.strip()) > max_len:
        error_msg.append(error_code)
        return None
    return value.strip() or None


def validate_display_fields(data, error_msg, prefix):
    """Fields shared by homepage display blocks (slider items, banners).

    Error codes are `<prefix>-<field>-invalid`. Returns model column kwargs.
    """
    media_id = data.get('media-id')
    if not is_int(media_id) or media_access.get(media_id) is None:
        error_msg.append(prefix + '-media-invalid')

    title = optional_str(data, 'title', 200, prefix + '-title-invalid', error_msg)
    subtitle = optional_str(data, 'subtitle', 300, prefix + '-subtitle-invalid', error_msg)
    link_url = optional_str(data, 'link-url', 500, prefix + '-link-url-invalid', error_msg)
    if link_url is not None and not LINK_URL_RE.match(link_url):
        error_msg.append(prefix + '-link-url-invalid')

    is_active = data.get('is-active', True)
    if not isinstance(is_active, bool):
        error_msg.append(prefix + '-is-active-invalid')
    sort_order = data.get('sort-order', 0)
    if not is_int(sort_order):
        error_msg.append(prefix + '-sort-order-invalid')

    starts_at, starts_ok = parse_datetime(data.get('starts-at'))
    ends_at, ends_ok = parse_datetime(data.get('ends-at'))
    if not starts_ok or not ends_ok:
        error_msg.append(prefix + '-dates-invalid')
    elif starts_at and ends_at and ends_at <= starts_at:
        error_msg.append(prefix + '-dates-order-invalid')

    return {'media_id': media_id,
            'title': title,
            'subtitle': subtitle,
            'link_url': link_url,
            'is_active': is_active,
            'sort_order': sort_order,
            'starts_at': starts_at,
            'ends_at': ends_at}
