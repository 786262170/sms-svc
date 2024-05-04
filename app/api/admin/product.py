# -*- coding: utf-8 -*-
import json
import time
import decimal

import sqlalchemy as sa

from typing import List
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from sdk import SmsStatus
from decimal import Decimal

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model.admin_user import AdminUser, AdminUserRole
from app.model import timestamp_to_datetime
from app.model.sms_product import SmsProduct, SmsProductType, SmsChannel, SmsProductProvider
from app.model.setting import Setting

router = APIRouter()

q = decimal.Decimal('1.000')

def round_cost_price(d: decimal.Decimal):
    return d.quantize(q, decimal.ROUND_DOWN)

class ProductResponse(OrmBaseModel):
    id: str = Field(..., description='产品ID')
    created_timestamp: int = Field(..., description='创建时间')

    admin_user_id: str = Field(..., description='用户ID')
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
                 admin_user_id: str = None,
                 country: str = None,
                 country_code: str = None,
                 provider: int = None,
                 type: int = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """产品列表"""
    current_user = session.info['current_user']

    q = session.query(SmsProduct)

    if current_user.role != AdminUserRole.SUPER.value:
        user_list = session.query(AdminUser).filter(
            AdminUser.parent_id == current_user.id).all()
        user_id_list = [x.id for x in user_list]

        q = q.filter(SmsProduct.admin_user_id.in_(user_id_list))

    if admin_user_id is not None:
        q = q.filter(SmsProduct.admin_user_id == admin_user_id)
    if country is not None:
        q = q.filter(SmsProduct.country == country)
    if country_code is not None:
        q = q.filter(SmsProduct.country_code == country_code)
    if provider is not None:
        q = q.filter(SmsProduct.provider == provider)
    if type is not None:
        q = q.filter(SmsProduct.tags.op('&')(type))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(SmsProduct.created_at >= timestamp_to_datetime(begin_timestamp),
                             SmsProduct.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(SmsProduct.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/price_list')
def product_price_list(admin_user_id: str = None,
                       country: str = None,
                       session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """价格列表"""
    current_user = session.info['current_user']

    if current_user.role == AdminUserRole.SUPER.value:
        user_list = session.query(AdminUser)
    else:
        user_list = session.query(AdminUser).filter(
            AdminUser.parent_id == current_user.id)

    if admin_user_id is not None:
        user_list = user_list.filter(AdminUser.id == admin_user_id)

    user_list = user_list.all()
    user_id_list = [x.id for x in user_list]

    q = session.query(SmsProduct.country,
                      SmsProduct.country_code,
                      SmsProduct.type,
                      sa.func.min(SmsProduct.price)
                      ).filter(SmsProduct.admin_user_id.in_(user_id_list))
    if country:
        q = q.filter(SmsProduct.country == country)

    rows = q.group_by(SmsProduct.country, SmsProduct.type).all()

    type_map = {
        SmsProductType.VERIFY.value: 'verify',
        SmsProductType.MESSAGING.value: 'sms',
        # // WHATS_APP ????
    }
    records = {}
    for row in rows:
        # row 分别为: country / country_code / type / price.
        item = records.get(row[0], {'country': row[0], 'country_code': row[1]})
        item[type_map.get(row[2])] = row[3]  # 记录该类型最便宜的价格
        records[row[0]] = item

    return records


@router.get('/price_list2')
def product_price_list2(admin_user_id: str = None,
                       country: str = None,
                       type: str = None,
                       channel: str = None,
                       session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """价格列表"""
    current_user = session.info['current_user']

    if current_user.role == AdminUserRole.SUPER.value:
        user_list = session.query(AdminUser)
    else:
        user_list = session.query(AdminUser).filter(
            AdminUser.parent_id == current_user.id)

    if admin_user_id is not None:
        user_list = user_list.filter(AdminUser.id == admin_user_id)

    user = user_list.first()

    q = session.query(SmsProduct.country,
                      SmsProduct.country_code,
                      SmsProduct.type,
                      SmsProduct.cost_price,
                      SmsProduct.channel_name,
                      SmsProduct.id
                      ).filter(SmsProduct.admin_user_id == user.id)
    if country:
        q = q.filter(SmsProduct.country == country)

    if type:
        q = q.filter(SmsProduct.type == type)

    if channel:
        q = q.filter(SmsProduct.channel_name == channel)

    rows = q.all()

    type_map = {
        SmsProductType.VERIFY.value: 'verify',
        SmsProductType.MESSAGING.value: 'sms',
        # // WHATS_APP ????
    }
    records = []
    for row in rows:
        parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == user.parent_id,
                                                          SmsProduct.country == row.country,
                                                          SmsProduct.type == row.type,
                                                          SmsProduct.channel_name == row.channel_name).first()
        # row 分别为: 国家 / 国际区号 / 类型(SMS/Verify/whatsApp) / 价格 / 通道名称
        item = {'country': row[0],
                'country_code': row[1],
                "cost_price": parent_product.cost_price,
                "type": type_map.get(row[2]),
                "price": row[3],
                "channel_name": row[4],
                "id": row[5]
                }
        records.append(item)

    return records


@router.get('/details/{id}', response_model=ProductResponse)
def product_details(id: str,
                    session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsProduct).filter(SmsProduct.id == id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.admin_user.parent_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    return product


# @router.delete('/details/{id}')
# def message_details(id: str,
#                     session: Session = Depends(GetSession(admin_login_required))):
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


class ProductRequest(BaseModel):
    # price: Decimal = Field(None, description='价格')
    cost_price: Decimal = Field(None, description='成本价格')


@router.put('/details/{id}', response_model=ProductResponse)
def product_modify(id: str,
                   data: ProductRequest,
                   session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsProduct).filter(SmsProduct.id == id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.admin_user.parent_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == current_user.id,
                                                      SmsProduct.country == product.country,
                                                      SmsProduct.type == product.type,
                                                      SmsProduct.channel_name == product.channel_name).first()

    if parent_product and parent_product.cost_price:
        if data.cost_price > parent_product.cost_price:
            raise BsException(BsExceptionEnum.PRICE_TOO_LOW, '价格比父级低')

    if data.cost_price is not None:
        product.cost_price = data.cost_price

    session.commit()
    return product


class ProductModifyPriceRequest(BaseModel):
    admin_user_id: str = Field(..., description='管理员用户ID')
    country: str = Field(..., description='国家')
    type: SmsProductType = Field(..., description=SmsProductType.__doc__)
    # price: Decimal = Field(None, description='价格')
    cost_price: Decimal = Field(None, description='成本价格')

class ProductModifyPrice2Request(BaseModel):
    id: str = Field(..., description='线路编号')
    admin_user_id: str = Field(..., description='管理员用户ID')
    cost_price: Decimal = Field(None, description='成本价格')

@router.put('/modify_price2', response_model=ProductResponse)
def product_modify_price2(data: ProductModifyPrice2Request,
                         session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改产品详情"""
    current_user = session.info['current_user']

    product = session.query(SmsProduct).filter(
        SmsProduct.id == data.id).first()

    setting = Setting.get_json(session, 'general_option')

    profit_rate_default = decimal.Decimal(
        setting['profit_rate_default']) / 100 + 1

    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.admin_user.parent_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == current_user.parent_id,
                                                      SmsProduct.country == product.country,
                                                      SmsProduct.type == product.type,
                                                      SmsProduct.channel_name == product.channel_name).first()

    if parent_product and parent_product.cost_price:
        if data.cost_price > parent_product.cost_price:
            raise BsException(BsExceptionEnum.PRICE_TOO_LOW, '价格比父级低')

    if data.cost_price is not None:
        product.cost_price = data.cost_price
        product.price = round_cost_price(product.cost_price * profit_rate_default)

    session.commit()
    return product

@router.put('/modify_price', response_model=ProductResponse)
def product_modify_price(data: ProductModifyPriceRequest,
                         session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改产品详情"""
    current_user = session.info['current_user']

    product = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == data.admin_user_id,
        SmsProduct.type == data.type.value,
        SmsProduct.country == data.country).order_by(SmsProduct.channel_price.asc()).first()

    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.admin_user.parent_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == current_user.id,
                                                      SmsProduct.country == product.country,
                                                      SmsProduct.type == product.type,
                                                      SmsProduct.channel_name == product.channel_name).first()

    if parent_product and parent_product.cost_price:
        if data.cost_price > parent_product.cost_price:
            raise BsException(BsExceptionEnum.PRICE_TOO_LOW, '价格比父级低')

    if data.cost_price is not None:
        product.cost_price = data.cost_price

    session.commit()
    return product

@router.get('/current_list', response_model=ProductList)
def product_current_list(page: int = 1,
                         per_page: int = 5,
                         country: str = None,
                         country_code: str = None,
                         provider: int = None,
                         type: int = None,
                         created_begin_timestamp: int = None,
                         created_end_timestamp: int = None,
                         session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """自己的产品列表"""
    current_user = session.info['current_user']

    q = session.query(SmsProduct)

    q = q.filter(SmsProduct.admin_user_id == current_user.id)
    if country is not None:
        q = q.filter(SmsProduct.country == country)
    if country_code is not None:
        q = q.filter(SmsProduct.country_code == country_code)
    if provider is not None:
        q = q.filter(SmsProduct.provider == provider)
    if type is not None:
        q = q.filter(SmsProduct.tags.op('&')(type))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(SmsProduct.created_at >= timestamp_to_datetime(begin_timestamp),
                             SmsProduct.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(SmsProduct.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/current_price_list')
def product_current_price_list(type: int = SmsProductType.VERIFY.value,
                               session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """自己的价格列表"""
    current_user = session.info['current_user']

    q = session.query(SmsProduct.country, sa.func.min(SmsProduct.price)).filter(
        SmsProduct.admin_user_id == current_user.id,
        SmsProduct.type.op('&')(type)).group_by(SmsProduct.country).all()

    ret = [{'country': x[0], 'price': x[1]} for x in q]

    return ret


@router.get('/current_details/{id}', response_model=ProductResponse)
def product_current_details(id: str,
                            session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """自己的产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsProduct).filter(
        SmsProduct.id == id, SmsProduct.admin_user_id == current_user.id).first()
    if product is None:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')
    return product


# @router.delete('/details/{id}')
# def message_details(id: str,
#                     session: Session = Depends(GetSession(admin_login_required))):
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


class ProductCurrentRequest(BaseModel):
    price: Decimal = Field(None, description='价格')
    # cost_price: Decimal = Field(None, description='成本价格')


@router.put('/current_details/{id}', response_model=ProductResponse)
def product_current_modify(id: str,
                           data: ProductCurrentRequest,
                           session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改自己的产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsProduct).filter(
        SmsProduct.id == id, SmsProduct.admin_user_id == current_user.id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if data.price is not None:
        product.price = data.price
    # if data.cost_price is not None:
    #     product.cost_price = data.cost_price

    session.commit()
    return product


class ProductCurrentModifyPriceRequest(BaseModel):
    country: str = Field(..., description='国家')
    type: SmsProductType = Field(..., description=SmsProductType.__doc__)
    price: Decimal = Field(None, description='价格')
    # cost_price: Decimal = Field(None, description='成本价格')


@router.put('/current_modify_price', response_model=ProductResponse)
def product_current_modify_price(data: ProductCurrentModifyPriceRequest,
                                 session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改自己的产品价格"""
    current_user = session.info['current_user']

    product = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == current_user.id,
        SmsProduct.type == data.type.value,
        SmsProduct.country == data.country).order_by(SmsProduct.channel_price.asc()).first()

    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if data.price is not None:
        product.price = data.price
    # if data.cost_price is not None:
    #     product.cost_price = data.cost_price

    session.commit()
    return product
