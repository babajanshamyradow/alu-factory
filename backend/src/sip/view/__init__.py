#!/usr/local/bin/python
# -*- coding: utf-8 -*-

"""Every public site endpoint is anonymous, so there is no `roles_required`
here — only the JSON envelope shared with the CRM."""

from backend.src.crm.view import api_response, json_response  # noqa: F401
