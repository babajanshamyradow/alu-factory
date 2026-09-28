#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from flask import Blueprint

from backend.src import contact_form
from backend.src.sip.view import api_response


bp = Blueprint('contact', __name__, url_prefix='/api')


@bp.route('/contact-messages', methods=['POST'])
@api_response
def contact_submit():
    """The site's contact form — the message lands in the console's Contact list."""
    return contact_form.submit_from_request()
