# -*- coding: utf-8 -*-
from fastapi.exceptions import HTTPException
from app.api import BsException, BsExceptionEnum
from typing import Dict
from app.model import app_config

import requests

TemplateData = Dict[str, str]


def send_mail_with_template(to: str,subject: str, template: str, data: TemplateData):
  resp = requests.post(
            app_config.EMAIL_API_URL,
            json={
                'from': app_config.EMAIL_FROM_ADDRESS,
                'to': to,
                'subject': subject,
                'template': template,
                'context': data,
                'secret': app_config.EMAIL_API_SECRET
            })
  if not resp.ok:
    raise HTTPException(resp.status_code, resp.json())
