#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import redis

from datetime import timedelta

from flask import Flask
from backend.src.db import db

def app_create(name, config):
    a = Flask(name)

    # SQL Alchemy Config
    # a.config['SQLALCHEMY_ECHO'] =  True
    a.config['SQLALCHEMY_DATABASE_URI'] = config['ALU_FACTORY'].get('DB_URI')
    a.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session Config
    a.config['SESSION_TYPE'] = 'redis'
    a.config['SESSION_REDIS'] = redis.from_url(config['ALU_FACTORY'].get('REDIS_URI'))
    a.config['SESSION_USE_SIGNER'] = True
    a.config['SESSION_COOKIE_HTTPONLY'] = True
    # FOR SSL only!!!
    a.config['SESSION_COOKIE_SECURE'] = False
    a.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)

    # App Params
    a.config['PORT'] = config['ALU_FACTORY'].get('CRM_PORT')
    a.config['REDIS_PREFIX'] = config['ALU_FACTORY'].get('REDIS_PREFIX')
    a.config['COMPANY_ID'] = config['ALU_FACTORY'].get('COMPANY_ID')

    # Folder Path
    a.config['MEDIA_UPLOAD_FOLDER'] = config['ALU_FACTORY'].get('MEDIA_UPLOAD_FOLDER')
    a.config['MEDIA_SERVE_URL'] = config['ALU_FACTORY'].get('MEDIA_SERVE_URL')
    a.config['APP_PATH'] = config['ALU_FACTORY'].get('APP_PATH')

    # Upload limits: per-type caps are checked in view/media.py; the global
    # cap makes Flask reject anything bigger (413) before reading it all.
    a.config['IMAGE_UPLOAD_MAX_SIZE_MB'] = config['ALU_FACTORY'].getint('IMAGE_UPLOAD_MAX_SIZE_MB', 5)
    a.config['ANY_UPLOAD_MAX_SIZE_MB'] = config['ALU_FACTORY'].getint('ANY_UPLOAD_MAX_SIZE_MB', 50)
    a.config['MAX_CONTENT_LENGTH'] = (a.config['ANY_UPLOAD_MAX_SIZE_MB'] + 1) * 1024 * 1024

    # Public contact form: max messages per IP per hour (view/contact.py).
    a.config['CONTACT_RATE_LIMIT_PER_HOUR'] = config['ALU_FACTORY'].getint('CONTACT_RATE_LIMIT_PER_HOUR', 5)

    a.config['COMPANY_NAME'] = config['ALU_FACTORY'].get('COMPANY_NAME')

    a.secret_key = config['ALU_FACTORY'].get('SECRET_KEY')
    a.debug = True

    db.init_app(a)
    a.db = db
    a.redis = redis.from_url(config['ALU_FACTORY'].get('REDIS_URI'))

    # Registering filters
    a.jinja_env.filters['number_to_words'] = number_to_words
    a.jinja_env.filters['weekday_to_str_tm'] = weekday_to_str_tm
    a.jinja_env.filters['weekday_to_str_ru'] = weekday_to_str_ru
    
    # Registering Blueprints
    from backend.src.crm.view.root import bp as root_bp
    a.register_blueprint(root_bp)
    from backend.src.crm.view.user import bp as user_bp
    a.register_blueprint(user_bp)
    from backend.src.crm.view.category import bp as category_bp
    a.register_blueprint(category_bp)
    from backend.src.crm.view.media import bp as media_bp
    a.register_blueprint(media_bp)
    from backend.src.crm.view.slider import bp as slider_bp
    a.register_blueprint(slider_bp)
    from backend.src.crm.view.product import bp as product_bp
    a.register_blueprint(product_bp)
    from backend.src.crm.view.banner import bp as banner_bp
    a.register_blueprint(banner_bp)
    from backend.src.crm.view.company import bp as company_bp
    a.register_blueprint(company_bp)
    from backend.src.crm.view.contact import bp as contact_bp
    a.register_blueprint(contact_bp)

    return a


def number_to_words(s):
    if s <= 0:
        return ""

    result = ''

    one_to_ten = { 1: 'bir', 2: 'iki', 3: 'üç', 4: 'dört', 5: 'bäş', 6: 'alty', 7: 'ýedi', 8: 'sekiz', 9: 'dokuz' }
    ten_to_hundred = { 1: 'on', 2: 'ýigrimi', 3: 'otuz', 4: 'kyrk', 5: 'elli', 6: 'altmyş', 7: 'ýetmiş', 8: 'segsen', 9: 'togsan' }
    hundred = 'ýüz'
    thousand = 'müň'

    a1 = a2 = a3 = a4 = a5 = a6 = 0
    r1 = r2 = r3 = r4 = r5 = r6 = 0

    # 123456 - a1 = 12345, r1 = 6, a2 = 1234, r2 = 5, a3 = 123, r3 = 4, a4 = 12, r4 = 3, a5 = 1, r5 = 2, a6 = 0, r6 = 1

    a1, r1 = divmod(s, 10)
    if a1 > 0:
        a2, r2 = divmod(a1, 10)
    if a2 > 0:
        a3, r3 = divmod(a2, 10)
    if a3 > 0:
        a4, r4 = divmod(a3, 10)
    if a4 > 0:
        a5, r5 = divmod(a4, 10)
    if a5 > 0:
        a6, r6 = divmod(a5, 10)

    if r6 > 0:
        result += '%s %s ' % (one_to_ten[r6], hundred)
    if r5 > 0:
        result += '%s ' % (ten_to_hundred[r5])
    if r4 > 0:
        result += '%s ' % (one_to_ten[r4])
    if r6 != 0 or r5 != 0 or r4!= 0:
        result += '%s ' % (thousand)
    if r3 > 0:
        result += '%s %s ' % (one_to_ten[r3], hundred)
    if r2 > 0:
        result += '%s ' % (ten_to_hundred[r2])
    if r1 > 0:
        result += '%s ' % (one_to_ten[r1])

    return result


def weekday_to_str_tm(day):
    try :
        day = int(day)
    except ValueError:
        return ""

    weekdays = {
        1: 'Duşenbe',
        2: 'Sişenbe',
        3: 'Çarşenbe',
        4: 'Penşenbe',
        5: 'Anna',
        6: 'Şenbe',
        7: 'Ýekşenbe'
    }

    if day in weekdays:
        return weekdays[day]
    
    return ''

def weekday_to_str_ru(day):
    try:
        day = int(day)
    except ValueError:
        return ""

    weekdays = {
        1: 'Понедельник',
        2: 'Вторник',
        3: 'Среда',
        4: 'Четверг',
        5: 'Пятница',
        6: 'Суббота',
        7: 'Воскресенье'
    }

    if day in weekdays:
        return weekdays[day]
    
    return ''
