# -*- coding: utf-8 -*-
import json
import time
import sqlalchemy as sa

from typing import List
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.model.sms_user import SmsUser
from sdk import SmsStatus
from decimal import Decimal

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model.user import User
from app.model.admin_user import AdminUser, AdminUserRole
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

    provider: SmsProductProvider = Field(..., description=SmsProductProvider.__doc__)
    type: SmsProductType = Field(..., description=SmsProductType.__doc__)

    price: Decimal = Field(..., description='价格')


class ProductList(PaginateBase):
    items: List[ProductResponse] = []


@router.get('/list', response_model=ProductList)
def product_list(page: int = 1,
                 per_page: int = 5,
                 user_id: str = None,
                 country: str = None,
                 country_code: str = None,
                 provider: int = None,
                 type: int = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """产品列表"""
    current_user = session.info['current_user']

    q = session.query(SmsUser)

    if current_user.role != AdminUserRole.SUPER.value:
        user_list = session.query(User).filter(User.admin_user_id == current_user.id).all()
        user_id_list = [x.id for x in user_list]

        q = q.filter(SmsUser.user_id.in_(user_id_list))

    if user_id is not None:
        q = q.filter(SmsUser.user_id == user_id)
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


@router.get('/price_list')
def product_price_list(user_id: str = None,
                       country: str = None,
                       type: int = SmsProductType.VERIFY.value,
                       session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """价格列表"""
    current_user = session.info['current_user']

    if current_user.role == AdminUserRole.SUPER.value:
        user_list = session.query(User)
    else:
        user_list = session.query(User).filter(User.admin_user_id == current_user.id)

    if user_id is not None:
        user_list = user_list.filter(User.id == user_id)

    user_list = user_list.all()
    user_id_list = [x.id for x in user_list]

    # 按照国家和类型划分,获取这里面所有最便宜的
    if user_list[0].get_default_channel_name(SmsProductType.VERIFY) is None :
        q = session.query(
            SmsUser.country,
            SmsUser.country_code,
            SmsUser.type,
            sa.func.min(SmsUser.price),
            SmsUser.default_price,
            SmsUser.user_id,
            SmsUser.channel_name).filter(SmsUser.user_id.in_(user_id_list),
                                  SmsUser.type == 1)
    else:
        q = session.query(
            SmsUser.country,
            SmsUser.country_code,
            SmsUser.type,
            SmsUser.price,
            SmsUser.default_price,
            SmsUser.user_id,
            SmsUser.channel_name).filter(SmsUser.user_id.in_(user_id_list),
                                  SmsUser.channel_name == user_list[0].get_default_channel_name(SmsProductType.VERIFY),
                                  SmsUser.type == 1
                                  )

    if user_list[0].get_default_channel_name(SmsProductType.MESSAGING) is None:
        q1 = session.query(
            SmsUser.country,
            SmsUser.country_code,
            SmsUser.type,
            sa.func.min(SmsUser.price),
            SmsUser.default_price,
            SmsUser.user_id,
            SmsUser.channel_name).filter(SmsUser.user_id.in_(user_id_list),
                                  SmsUser.type == 2)
    else:
        q1 = session.query(
            SmsUser.country,
            SmsUser.country_code,
            SmsUser.type,
            SmsUser.price,
            SmsUser.default_price,
            SmsUser.user_id,
            SmsUser.channel_name).filter(SmsUser.user_id.in_(user_id_list),
                                  SmsUser.channel_name == user_list[0].get_default_channel_name(SmsProductType.MESSAGING),
                                  SmsUser.type == 2)

    if country:
        q = q.filter(SmsUser.country == country)
        q1 = q1.filter(SmsUser.country == country)

    rows = q.group_by(SmsUser.country, SmsUser.type).all()
    rows += q1.group_by(SmsUser.country, SmsUser.type).all()

    type_map = {
        SmsProductType.VERIFY.value: 'verify',
        SmsProductType.MESSAGING.value: 'sms',
        # // WHATS_APP ????
    }
    records = {}
    parent_user = None
    for row in rows:
        if parent_user is None:
            parent_user = session.query(User.admin_user_id).filter(User.id == row[5]).first()
        # row 分别为: country / country_code / type / price.
        item = records.get(row[0], {'country': row[0], 'country_code': row[1]})
        item[type_map.get(row[2])] = row[3]  # 记录该类型最便宜的价格
        item[type_map.get(row[2])+'_default_price'] = row[4]
        product = session.query(SmsProduct.cost_price,SmsProduct.type).filter(SmsProduct.admin_user_id == parent_user.admin_user_id,
                                                    SmsProduct.country == row[0],
                                                    SmsProduct.country_code == row[1],
                                                    SmsProduct.channel_name == row[6]).first()
        item[type_map.get(product.type)+'cost_price'] = product.cost_price
        records[row[0]] = item

    return records

    # price_list = []
    # for user_id in user_id_list:
    #     q = session.query(SmsUser.country, sa.func.min(SmsUser.price)).filter(
    #         SmsUser.user_id == user_id,
    #         SmsUser.type.op('&')(type)).group_by(SmsUser.country).all()

    #     price_list.append({'user_id': user_id, 'content': [{'country': x[0], 'price': x[1]} for x in q]})

    # return price_list


@router.get('/details/{id}', response_model=ProductResponse)
def product_details(id: str,
                    session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """产品详情"""
    current_user = session.info['current_user']
    product = session.query(SmsUser).filter(SmsUser.id == id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.user.admin_user_id != current_user.id:
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
    price: Decimal = Field(..., description='价格')


@router.put('/details/{id}', response_model=ProductResponse)
def product_modify(id: str,
                   data: ProductRequest,
                   session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改产品详情"""
    current_user: AdminUser = session.info['current_user']
    product = session.query(SmsUser).filter(SmsUser.id == id).first()
    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.user.admin_user_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == product.user.admin_user_id,
                                                      SmsProduct.country == product.country,
                                                      SmsProduct.type == product.type,
                                                      SmsProduct.channel_name == product.channel_name).first()

    if data.price < parent_product.cost_price:
        raise BsException(BsExceptionEnum.PRICE_TOO_LOW, '价格比父级低')

    product.price = data.price

    session.commit()
    return product


class ProductModifyPriceRequest(BaseModel):
    user_id: str = Field(..., description='用户ID')
    country: str = Field(..., description='国家')
    type: SmsProductType = Field(..., description=SmsProductType.__doc__)
    price: Decimal = Field(..., description='价格')


@router.put('/modify_price', response_model=ProductResponse)
def product_modify_price(data: ProductModifyPriceRequest,
                         session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_AGENT))):
    """修改产品价格"""
    current_user: AdminUser = session.info['current_user']

    if data.user_id is not None:
       user = session.query(User).filter(User.id == data.user_id).first()

    if data.type.value == 1:
        if user.get_default_channel_name(SmsProductType.VERIFY) is None:
            product = session.query(SmsUser).filter(
                SmsUser.user_id == data.user_id,
                SmsUser.type == data.type.value,
                SmsUser.country == data.country).order_by(SmsUser.price.asc()).first()
        else:
            product = session.query(SmsUser).filter(
                SmsUser.user_id == data.user_id,
                SmsUser.type == data.type.value,
                SmsUser.country == data.country,
                SmsUser.channel_name == user.get_default_channel_name(SmsProductType.VERIFY)).first()
    else:
        if user.get_default_channel_name(SmsProductType.MESSAGING) is None :
            product = session.query(SmsUser).filter(
                SmsUser.user_id == data.user_id,
                SmsUser.type == data.type.value,
                SmsUser.country == data.country).order_by(SmsUser.price.asc()).first()
        else:
            product = session.query(SmsUser).filter(
                SmsUser.user_id == data.user_id,
                SmsUser.type == data.type.value,
                SmsUser.country == data.country,
                SmsUser.channel_name == user.get_default_channel_name(SmsProductType.MESSAGING)).first()

    if not product:
        raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    if current_user.role != AdminUserRole.SUPER:
        if product.user.admin_user_id != current_user.id:
            raise BsException(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品不存在')

    parent_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == product.user.admin_user_id,
                                                      SmsProduct.country == product.country,
                                                      SmsProduct.type == product.type,
                                                      SmsProduct.channel_name == product.channel_name).first()

    if data.price < parent_product.cost_price:
        raise BsException(BsExceptionEnum.PRICE_TOO_LOW, '价格比父级低')

    product.price = data.price

    session.commit()
    return product
