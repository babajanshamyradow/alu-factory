#!/usr/local/bin/python
# -*- coding: utf-8 -*-

config = {
  'name': 'Alumni Management System',
  'description': 'Alumni Management System',
  'author': 'Babajan Shamyradov <babajanshamyradow98@gmail.com>',
  'author_email': 'babajanshamyradow98@gmail.com',
  'version': '0.1',
  'install_requires': ['flask', 'psycopg2-binary', 'flask-sqlalchemy', 'passlib', 'pycrypto', 'redis', 'pillow', 'xlsxwriter', 'pyotp', 'python-docx', 'docxtpl', 'flask-httpauth', 'python-magic', 'pycountry', 'qrcode'],
  'tests_require': ['nose', 'mock', 'coverage'],
  'test_suite': 'nose.collector',
  'include_package_data': True,
  'zip_safe': False,
  'scripts': [],
  'entry_points': {
    'console_scripts': [
       'crm = backend.src.crm:run',
       'sip = backend.src.sip:run'
    ]
  }
}

try:
    import setuptools
    packages = setuptools.find_packages()
    config['packages'] = packages
    setuptools.setup(**config)
except ImportError:
    from distutils import core
    core.setup(**config)
