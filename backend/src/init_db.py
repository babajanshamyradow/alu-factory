#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from backend.src import model
from backend.src.crm.web import app

if __name__ == '__main__':
    with app.app_context():
        model.remove_db()
        model.init_db()
        model.fill_default()
        model.fill_temp()
