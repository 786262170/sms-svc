# -*- coding: utf-8 -*-
import datetime
import hashlib

from fastapi import HTTPException
from pydantic import Field
from pydantic.main import BaseModel

from app.model.application import Application


class SmsBaseRequest(BaseModel):
    app_id: str = Field(..., description='app_id')
    datetime: int = Field(..., description='请求时间')
    sign: str = Field(..., description='签名')


def sms_login_required(data: SmsBaseRequest, session) -> Application:
    now = datetime.datetime.now()
    datetime_int = int(datetime.datetime.strftime(now, '%Y%m%d%H%M%S'))
    app = session.query(Application).get(data.app_id)
    if not app:
        raise HTTPException(status_code=401)
    if data.datetime > datetime_int + 500 or data.datetime < datetime_int - 500:
        raise HTTPException(status_code=401)

    signature_content = data.app_id + str(data.datetime) + app.app_key
    signature_content = signature_content.encode('utf-8')
    expected_signature = hashlib.md5(signature_content).hexdigest()
    if expected_signature != data.sign:
        raise HTTPException(status_code=401)

    return app
