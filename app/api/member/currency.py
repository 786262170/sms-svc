# -*- coding: utf-8 -*-
import json
import requests

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, Form
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import get_db, BsException, BsExceptionEnum, app_config

router = APIRouter()


@router.get('/usd2cny')
def contact_details(session: Session = Depends(get_db)):
    """美元对人民币汇率获取"""

    r = requests.post(app_config.DIZPAY_QUERY_CURRENCY, json=dict(currency_list='CNY'))

    if r.status_code == requests.codes.ok:
        if r.encoding is None or r.encoding == 'ISO-8859-1':
            r.encoding = 'UTF-8'
        return r.json().get('objects')[0]
    else:
        raise BsException(BsExceptionEnum.CURRENCY_NOT_EXIST, r.text)

