# -*- coding: utf-8 -*-
import io
import json
from io import StringIO

import time
import pandas as pd
import sqlalchemy as sa

from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session
from starlette.responses import Response, StreamingResponse

from app.model.sms_user import SmsUser
from sdk import SmsStatus
from decimal import Decimal

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.member import member_login_required, country_dict
from app.model import timestamp_to_datetime
from app.model.sms_product import SmsProduct, SmsProductType, SmsChannel, SmsProductProvider

router = APIRouter()


class ProductResponse(OrmBaseModel):
    id: str = Field(..., description='产品ID')
    created_timestamp: int = Field(..., description='创建时间')

    user_id: str = Field(..., description='用户ID')
    channel_name: str = Field(..., description='应用名称')

    country: str = Field(..., description='国家')
    country_code: str = Field(..., description='国家代码')

    provider: SmsProductProvider = Field(...,
                                         description=SmsProductProvider.__doc__)
    type: SmsProductType = Field(..., description=SmsProductType.__doc__)

    price: Decimal = Field(..., description='价格')


class ProductList(PaginateBase):
    items: List[ProductResponse] = []


@router.get('/list', response_model=ProductList)
def product_list(page: int = 1,
                 per_page: int = 5,
                 country: str = None,
                 country_code: str = None,
                 provider: int = None,
                 type: int = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(member_login_required))):
    """产品列表"""
    current_user = session.info['current_user']
    q = session.query(SmsUser)
    q = q.filter(SmsUser.user_id == current_user.id)
    if country is not None:
        q = q.filter(SmsUser.country == country)
    if country_code is not None:
        q = q.filter(SmsUser.country_code == country_code)
    if provider is not None:
        q = q.filter(SmsUser.provider == provider)
    if type is not None:
        q = q.filter(SmsUser.tags.op('&')(type))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(SmsUser.created_at >= timestamp_to_datetime(begin_timestamp),
                             SmsUser.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(SmsUser.created_at.desc())
    return q.paginate(page, per_page)


class PriceListResponse(OrmBaseModel):
    country: str = Field(..., description='国家码')
    country_cn: str = Field(..., description='国家中文')
    country_en: str = Field(..., description='国家码英文')
    code: str = Field(..., description='区号')
    price: Decimal = Field(..., description='价格')


@router.get('/price_list', response_model=List[PriceListResponse])
def product_price_list(type: int = Query(SmsProductType.VERIFY.value, description=SmsProductType.__doc__),
                       country: str = Query(None, description='国家'),
                       session: Session = Depends(GetSession(member_login_required))):
    """价格列表"""
    current_user = session.info['current_user']

    q = session.query(SmsUser.country, SmsUser.country_code, sa.func.min(SmsUser.price)).filter(
        SmsUser.user_id == current_user.id,
        SmsUser.type.op('&')(type)).group_by(SmsUser.country, SmsUser.country_code)
    if country:
        q = q.filter(SmsUser.country == country)

    ret = [{'country': x[0],
            'country_cn': country_dict[x[0]]['cn'],
            'country_en': country_dict[x[0]]['en'],
            'code': x[1],
            'price': x[2]} for x in q.all()]

    return ret


@router.get('/price_download', response_description='xlsx')
def price_download(type: int = Query(SmsProductType.VERIFY.value, description=SmsProductType.__doc__),
                   session: Session = Depends(GetSession(member_login_required))):
    """价格列表"""
    current_user = session.info['current_user']

    q = session.query(SmsUser.country, SmsUser.country_code, sa.func.min(SmsUser.price)).filter(
        SmsUser.user_id == current_user.id,
        SmsUser.type.op('&')(type)).group_by(SmsUser.country, SmsUser.country_code).all()

    ret = [{'country': x[0],
            'country_cn': country_dict[x[0]]['cn'],
            'country_en': country_dict[x[0]]['en'],
            'code': x[1],
            'price': x[2]} for x in q]
    df = pd.DataFrame(ret)
    bio = io.BytesIO()
    writer = pd.ExcelWriter(bio, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.save()
    bio.seek(0)
    headers = {
        'Content-Disposition': 'attachment; filename="price.xlsx"'
    }
    return StreamingResponse(bio, headers=headers)


@router.get('/details/{id}', response_model=ProductResponse)
def product_details(id: str,
                    session: Session = Depends(GetSession(member_login_required))):
    """产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsUser).filter(SmsUser.user_id == current_user.id,
                                            SmsUser.id == id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    return product

# @router.delete('/details/{id}')
# def message_details(id: str,
#                     session: Session = Depends(GetSession(member_login_required))):
#     """删除产品"""
#     current_user = session.info['current_user']
#     message = session.query(Message).filter(Message.user_id == current_user.id,
#                                             Message.id == id).first()
#     if not message:
#         raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '短信不存在')
#
#     # session.delete(message)
#     message.invalid = 1
#     session.commit()
#
#     return {}
