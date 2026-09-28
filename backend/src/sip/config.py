#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import redis

from flask import Flask
from backend.src.db import db

def app_create(name, config):
    a = Flask(name)

    # SQL Alchemy Config
    a.config['SQLALCHEMY_DATABASE_URI'] = config['ALU_FACTORY'].get('DB_URI')
    a.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # App Params
    a.config['PORT'] = config['ALU_FACTORY'].get('SIP_PORT')
    a.config['REDIS_PREFIX'] = config['ALU_FACTORY'].get('REDIS_PREFIX')

    # Folder Path
    a.config['MEDIA_UPLOAD_FOLDER'] = config['ALU_FACTORY'].get('MEDIA_UPLOAD_FOLDER')

    # The site only receives small JSON bodies (contact form).
    a.config['MAX_CONTENT_LENGTH'] = 64 * 1024

    # Public contact form: max messages per IP per hour (contact_form.py).
    a.config['CONTACT_RATE_LIMIT_PER_HOUR'] = config['ALU_FACTORY'].getint('CONTACT_RATE_LIMIT_PER_HOUR', 5)

    a.secret_key = config['ALU_FACTORY'].get('SECRET_KEY')

    db.init_app(a)
    a.db = db
    a.redis = redis.from_url(config['ALU_FACTORY'].get('REDIS_URI'))

    # Registering Blueprints
    from backend.src.sip.view.root import bp as root_bp
    a.register_blueprint(root_bp)
    from backend.src.sip.view.company import bp as company_bp
    a.register_blueprint(company_bp)
    from backend.src.sip.view.showcase import bp as showcase_bp
    a.register_blueprint(showcase_bp)
    from backend.src.sip.view.catalog import bp as catalog_bp
    a.register_blueprint(catalog_bp)
    from backend.src.sip.view.contact import bp as contact_bp
    a.register_blueprint(contact_bp)

    return a
