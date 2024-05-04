# -*- coding: utf-8 -*-
import json
import logging
from decimal import Decimal
from typing import List

import phonenumbers
from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy.orm import Session

from app.api import get_db, OrmBaseModel, BsException, BsExceptionEnum
from app.api.sms import SmsBaseRequest, sms_login_required
from app.model.message import Message, MessageCheck
from app.model.sms_product import SmsProductType
from app.model.sms_user import SmsUser
from app.model.user import User
from sdk import SmsStatus
from sdk.sms_api import SmsApi

router = APIRouter()


class BalanceResponse(OrmBaseModel):
    balance: Decimal = Field(..., description='余额')


@router.post("/get_balance", response_model=BalanceResponse)
def get_balance(data: SmsBaseRequest,
                session: Session = Depends(get_db)):
    app = sms_login_required(data, session)
    return app.user


class VerifyMessageRequest(SmsBaseRequest):
    mobile: str = Field(..., description='手机号')
    content: str = Field(..., description='短信内容')


class MessageResponse(OrmBaseModel):
    id: str = Field(..., description='信息ID')
    mobile: str = Field(..., description='手机号')


@router.post('/send_verify', response_model=MessageResponse)
def send_verify(data: VerifyMessageRequest,
                session: Session = Depends(get_db)):
    """发送验证短信"""
    app = sms_login_required(data, session)
    current_user: User = app.user

    # 优先使用用户传递进来的内容，如没传内容则必须使用模板
    # if data.content is not None:
    #     content = data.content
    # elif data.message_template_id is not None:
    #     message_template = session.query(MessageTemplate).filter(
    #         MessageTemplate.id == data.message_template_id,
    #         MessageTemplate.invalid == 0,
    #         MessageTemplate.status == MessageTemplateStatus.SUCCESS.value).first()
    #     if not message_template:
    #         raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')
    #
    #     if message_template.shared == 0 and message_template.user_id != current_user.id:
    #         raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')
    #
    #     code = str(random.randint(100000, 999999))
    #     content = message_template.content.format(code=code)  # 根据模板内容生成验证码
    # else:
    #     raise BsException(BsExceptionEnum.MESSAGE_CONTENT_EMPTY, '短信内容为空')

    # if len(data.mobile) != 1:
    #     raise BsException(BsExceptionEnum.PARAMETER_ERROR, '请求参数错误')
    mobile = data.mobile

    mobile, price, product = SmsUser.phone_get_price_product(session, current_user, mobile,
                                                             SmsProductType.VERIFY)

    # 判断冻结的金额是否大于余额，是的话不允许发送
    ret = session.query(User).filter(User.id == current_user.id,
                                     User.balance > User.frozen_balance + price).update(
        dict(frozen_balance=User.frozen_balance + price))
    if ret != 1:
        raise BsException(BsExceptionEnum.API_BALANCE_NOT_ENOUGH, '余额不足')

    message = Message(user_id=current_user.id,
                      app_id=data.app_id,
                      mobile=json.dumps(data.mobile),
                      content=data.content)

    session.add(message)
    session.flush()

    # sms发送接口
    sms_api = SmsApi(product.provider, product.channel.app_id, product.channel.app_key)
    phone_list = [mobile]
    result_list = sms_api.send_sms_chunked(phone_list, data.content)

    # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
    message_check = MessageCheck(user_id=current_user.id,
                                 message_id=message.id,
                                 sms_product_id=product.id,
                                 country=product.country,
                                 content=data.content,
                                 phone_number=result_list[0]['phone'],
                                 message_number=result_list[0]['id'],
                                 price=price)
    session.add(message_check)
    session.commit()

    return message_check


class MessagingRequest(SmsBaseRequest):
    mobile: List[str] = Field(..., description='手机号')
    content: str = Field(..., description='短信内容')


@router.post('/send_message', response_model=List[MessageResponse])
def send_message(data: MessagingRequest,
                 session: Session = Depends(get_db)):
    """发送营销短信"""
    app = sms_login_required(data, session)
    current_user: User = app.user
    content = data.content
    # 此处接口手机号支持''也支持[],但必须只有一个手机号码,通过phonenumbers获取手机区号
    country_phone_dict = {}
    for item in data.mobile:
        mobile = item

        mobile = '+{}'.format(mobile)
        number = phonenumbers.parse(mobile)
        country = phonenumbers.region_code_for_number(number)  # 可获取国家名称
        country_code = number.country_code
        mobile = number.national_number

        phone_number = '{}{}'.format(country_code, mobile)

        if country_phone_dict.get(country) is None:
            country_phone_dict.update({country: [phone_number]})
        else:
            country_phone_dict[country].append(phone_number)

    # 查找最适合的sms产品
    country_list = [country for country in country_phone_dict]
    price_product_dict = SmsUser.country_get_price_product(session, current_user, country_list,
                                                           SmsProductType.MESSAGING)

    amount = 0
    for country in country_phone_dict:
        phone_list = country_phone_dict[country]
        amount += price_product_dict[country]['price'] * len(phone_list)

    # 判断冻结的金额是否大于余额，是的话不允许发送
    ret = session.query(User).filter(User.id == current_user.id,
                                     User.balance > User.frozen_balance + amount).update(
        dict(frozen_balance=User.frozen_balance + amount))
    if ret != 1:
        raise BsException(BsExceptionEnum.API_BALANCE_NOT_ENOUGH, '余额不足')

    message = Message(user_id=current_user.id,
                      app_id=data.app_id,
                      mobile=json.dumps(data.mobile),
                      content=content)

    session.add(message)
    session.flush()

    result_check_list = []
    for country in country_phone_dict:
        phone_list = country_phone_dict[country]
        price = price_product_dict[country]['price']
        sms_product = price_product_dict[country]['product']

        # sms发送接口
        sms_api = SmsApi(sms_product.provider, sms_product.channel.app_id, sms_product.channel.app_key)

        try:
            result_list = sms_api.send_sms_chunked(phone_list, content)
        except Exception as e:
            logging.error('messaging error exception: {}'.format(e))
            result_list = []
            for phone in phone_list:
                result_list.append({'phone': phone, 'id': None})

        for result_dict in result_list:
            # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
            message_check = MessageCheck(user_id=current_user.id,
                                         message_id=message.id,
                                         sms_product_id=sms_product.id,
                                         country=sms_product.country,
                                         phone_number=result_dict['phone'],
                                         message_number=result_dict['id'],
                                         content=content,
                                         price=price)
            session.add(message_check)
            result_check_list.append(message_check)
    session.commit()

    return result_check_list


class QueryRequest(SmsBaseRequest):
    id_list: List[str] = Field(..., description='信息ID列表')


class QueryResponse(OrmBaseModel):
    id: str = Field(..., description='信息ID')
    mobile: str = Field(..., description='手机号')
    message_status: SmsStatus = Field(..., description=str(SmsStatus.__doc__))


@router.post('/query', response_model=List[QueryResponse])
def query_message(data: QueryRequest,
                  session: Session = Depends(get_db)):
    """查询短信"""
    app = sms_login_required(data, session)
    result = session.query(MessageCheck).filter(MessageCheck.id.in_(data.id_list),
                                                MessageCheck.user_id == app.user_id).all()
    return result
