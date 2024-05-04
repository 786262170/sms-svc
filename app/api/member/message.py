# -*- coding: utf-8 -*-
import datetime
import io
import json
import logging
import random
import time
from decimal import Decimal
from typing import List, Optional, TypeVar

import app.utils.xlsx as xlsx_utils
import pandas as pd
import phonenumbers
import sqlalchemy as sa
from app.api import (BsException, BsExceptionEnum, BsExceptionWithNumbers, GetSession, OrmBaseModel,
                     PaginateBase)
from app.api.member import get_country_name, member_login_required
from app.model import (date_datetime, datetime_from_str_time,
                       datetime_to_str_time, datetime_to_timestamp,
                       timestamp_to_datetime)
from app.model.application import Application
from app.model.contact import Contact
from app.model.message import (Message, MessageCheck, MessageStatus,
                               MessageTemplate, MessageTemplateStatus,
                               MessageTiming, MessageTimingFrequency,
                               MessageType)
from app.model.sms_product import SmsProduct, SmsProductType
from app.model.sms_user import SmsUser
from app.model.user import User
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sdk import SmsStatus
from sdk.sms_api import SmsApi
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

router = APIRouter()


# class UserResponse(OrmBaseModel):
#     id: str
#     uid: str
#     avatar: str = None
#     nickname: str = None
#     name: str = None
#
#
# class ApplicationResponse(OrmBaseModel):
#     app_id: str = Field(..., description='应用ID')
#     name: str = Field(..., description='应用名称')


class MessageResponse(OrmBaseModel):
    id: str = Field(..., description='消息ID')
    created_timestamp: int = Field(..., description='创建时间')

    group_id: int = Field(None, description='联系人组ID')

    content: str = Field(..., description='区号')
    mobile: str = Field(..., description='手机号码')
    filtered_mobile: str = Field(None, description='被过滤的手机号码')
    # user = UserResponse
    # application = ApplicationResponse


class MessageList(PaginateBase):
    items: List[MessageResponse] = []


@router.get('/message_list', response_model=MessageList)
def message_list(page: int = 1,
                 per_page: int = 5,
                 app_id: str = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(member_login_required))):
    """短信列表"""
    current_user = session.info['current_user']
    q = session.query(Message)
    q = q.filter(Message.user_id == current_user.id)
    if app_id is not None:
        q = q.filter(Message.app_id == app_id)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(Message.created_at >= timestamp_to_datetime(begin_timestamp),
                             Message.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(Message.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/message_details/{id}', response_model=MessageResponse)
def message_details(id: str,
                    session: Session = Depends(GetSession(member_login_required))):
    """短信详情"""
    current_user = session.info['current_user']
    message = session.query(Message).filter(Message.user_id == current_user.id,
                                            Message.id == id).first()
    if not message:
        raise BsException(BsExceptionEnum.MESSAGE_NOT_EXIST, '短信不存在')

    return message


# @router.delete('/details/{id}')
# def message_details(id: str,
#                     session: Session = Depends(GetSession(member_login_required))):
#     """删除短信"""
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


class MessageTimingResponse(OrmBaseModel):
    id: str = Field(..., description='定时消息ID')
    created_timestamp: int = Field(..., description='创建时间')

    group_id: int = Field(None, description='联系人组ID')

    content: str = Field(..., description='区号')
    mobile: str = Field(..., description='手机号码')

    timing_timestamp: int = Field(...,
                                  description='定时的时间戳,如定时9点，就给当天日期的9点的时间戳')
    frequency: MessageTimingFrequency = Field(
        ..., description=MessageTimingFrequency.__doc__)

    processed_timestamp: Optional[int] = Field(None, description='被处理的时间戳')
    delivered_count: Optional[int] = Field(None, description='实际发送数量')

    # user = UserResponse
    # application = ApplicationResponse


class MessageTimingList(PaginateBase):
    items: List[MessageTimingResponse] = []


MESSAGE_TIMING_LIST_EXPORT_FIELDS = [
    xlsx_utils.GenerateField(
        MessageTiming.created_at,
        '发送时间'),
    xlsx_utils.GenerateField(
        MessageTiming.group_id,
        '联系人组 ID'
    ),
    xlsx_utils.GenerateField(
        MessageTiming.mobile,
        '号码'
    ),
    xlsx_utils.GenerateField(
        MessageTiming.content,
        '内容'
    ),
    xlsx_utils.GenerateField(
        MessageTiming.timing_at,
        '定时发送时间'),
    xlsx_utils.GenerateField(
        MessageTiming.frequency,
        '频次'
    )
]


@router.get('/message_timing_list', response_model=MessageTimingList)
def message_timing_list(page: int = 1,
                        per_page: int = 5,
                        export: bool = Query(None, description='导出数据'),
                        # app_id: str = None,
                        invalid: int = Query(
                            None, description='无效标记，0为查询有效，1为查询无效'),
                        created_begin_timestamp: int = None,
                        created_end_timestamp: int = None,
                        session: Session = Depends(GetSession(member_login_required))):
    """定时短信列表"""
    current_user = session.info['current_user']
    q = session.query(MessageTiming)
    q = q.filter(MessageTiming.user_id == current_user.id)
    # if app_id is not None:
    #     q = q.filter(MessageTiming.app_id == app_id)
    if invalid is not None:
        q = q.filter(MessageTiming.invalid == invalid)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(MessageTiming.created_at >= timestamp_to_datetime(begin_timestamp),
                             MessageTiming.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(MessageTiming.created_at.desc())
    if export:
        headers = {
            'Content-Disposition': 'attachment; filename="messages.xlsx"'
        }
        return StreamingResponse(
            xlsx_utils.generate_xlsx_stream(
                q.all(),
                MESSAGE_TIMING_LIST_EXPORT_FIELDS),
            headers=headers)
    return q.paginate(page, per_page)


@router.get('/message_timing_details/{id}', response_model=MessageTimingResponse)
def message_timing_details(id: str,
                           session: Session = Depends(GetSession(member_login_required))):
    """定时短信详情"""
    current_user = session.info['current_user']
    message_timing = session.query(MessageTiming).filter(MessageTiming.user_id == current_user.id,
                                                         MessageTiming.id == id).first()
    if not message_timing:
        raise BsException(BsExceptionEnum.MESSAGE_NOT_EXIST, '短信不存在')

    return message_timing


@router.delete('/message_timing_details/{id}')
def message_timing_details(id: str,
                           session: Session = Depends(GetSession(member_login_required))):
    """删除定时短信"""
    current_user = session.info['current_user']
    message_timing = session.query(MessageTiming).filter(MessageTiming.user_id == current_user.id,
                                                         MessageTiming.invalid == 0,
                                                         MessageTiming.id == id).first()
    if not message_timing:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '短信不存在')

    # session.delete(message_timing)
    message_timing.invalid = 1
    session.commit()

    return {}


class TimingMessageRequest(BaseModel):
    # app_id: str = Field(..., description='应用ID')

    type: MessageType = Field(..., description=MessageType.__doc__)

    group_id: int = Field(None, description='联系人组ID, 只有营销短信可以填写，和手机号二选一，手机号优先')
    mobile: List[str] = Field(None, description='手机号')
    filtered_mobile: List[str] = Field(None, description='过滤的手机号')
    content: str = Field(None, description='短信内容,和模板二选一填写')
    message_template_id: str = Field(None, description='短信模板ID,和内容二选一填写')

    timing_timestamp: int = Field(..., description='定时的时间戳')

    frequency: MessageTimingFrequency = Field(
        ..., description=MessageTimingFrequency.__doc__)

    # channel_name: str = Field(None, description='通道名称（当前版本不传）')


@router.post('/send_timing_message', response_model=MessageResponse)
def send_timing_message(data: TimingMessageRequest,
                        session: Session = Depends(GetSession(member_login_required))):
    """发送定时群发(营销)短信"""
    current_user: User = session.info['current_user']

    # app = session.query(Application).filter(Application.app_id == data.app_id).first()
    app = Application.default_get(session, current_user.id)
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    group_id = None
    # 只有营销可以用联系人组的方式来发送
    if data.type == MessageType.NORMAL:
        if data.mobile is None or len(data.mobile) == 0:
            raise BsException(BsExceptionEnum.MOBILE_NOT_EXIST, '手机号或联系人组不存在')
        mobile_list = data.mobile
    else:
        if data.mobile is not None and len(data.mobile) != 0:
            mobile_list = data.mobile
        elif data.group_id is not None:
            contact_list = session.query(Contact).filter(Contact.user_id == current_user.id,
                                                         Contact.group_id == data.group_id).all()
            if contact_list is None or len(contact_list) == 0:
                raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '联系人组不存在')
            mobile_list = [x.mobile for x in contact_list]
            group_id = data.group_id
        else:
            raise BsException(BsExceptionEnum.MOBILE_NOT_EXIST, '手机号或联系人组不存在')

    # 优先使用用户传递进来的内容，如没传内容则必须使用模板
    if data.content is not None:
        content = data.content
    elif data.message_template_id is not None:
        message_template = session.query(MessageTemplate).filter(
            MessageTemplate.id == data.message_template_id,
            MessageTemplate.type == data.type.value,
            MessageTemplate.invalid == 0,
            MessageTemplate.status == MessageTemplateStatus.SUCCESS.value).first()
        if not message_template:
            raise BsException(
                BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

        if message_template.shared == 0 and message_template.user_id != current_user.id:
            raise BsException(
                BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

        content = message_template.content
    else:
        raise BsException(BsExceptionEnum.MESSAGE_CONTENT_EMPTY, '短信内容为空')

    message_timing = MessageTiming(user_id=current_user.id,
                                   app_id=app.app_id,
                                   group_id=group_id,
                                   type=data.type.value,
                                   mobile=json.dumps(mobile_list),
                                   mobile_count=0 if not mobile_list else len(
                                       mobile_list),
                                   content=content,
                                   timing_at=datetime.datetime.fromtimestamp(
                                       data.timing_timestamp),
                                   frequency=data.frequency.value)

    session.add(message_timing)
    session.commit()

    return message_timing


class SmsProductResponse(OrmBaseModel):
    id: str = Field(..., description='产品ID')
    country: str = Field(..., description='国家')
    country_code: int = Field(..., description='国家代码')


class MessageCheckResponse(OrmBaseModel):
    created_timestamp: int = Field(..., description='创建时间')

    phone_number: str = Field(..., description='手机号')
    message_number: str = Field(None, description='短信发送返回号')
    message_status: SmsStatus = Field(..., description=str(SmsStatus.__doc__))

    price: Decimal = Field(..., description='价格')

    content: str = Field(..., description='内容')

    sms_product: SmsProductResponse

    message_timing: MessageTimingResponse = None


class MessageCheckList(PaginateBase):
    items: List[MessageCheckResponse] = []


MESSAGE_CHECK_LIST_EXPORT_FIELDS = [
    xlsx_utils.GenerateField(
        MessageCheck.created_at,
        '创建时间'),
    xlsx_utils.GenerateField(
        MessageCheck.country,
        '国家',
        lambda code: get_country_name(code)
    ),
    xlsx_utils.GenerateField(
        MessageCheck.phone_number,
        '号码'
    ),
    xlsx_utils.GenerateField(
        MessageCheck.message_number,
        '发送返回号'
    ),
    xlsx_utils.GenerateField(
        MessageCheck.content,
        '内容'
    ),
    xlsx_utils.GenerateField(
        MessageCheck.price,
        '价格'
    ),
    xlsx_utils.GenerateField(
        MessageCheck.message_status,
        '状态'
    )
]


@router.get('/message_check_list', response_model=MessageCheckList)
def message_check_list(page: int = 1,
                       per_page: int = 5,
                       export: bool = Query(None, description='导出数据'),
                       phone_number: str = Query(None, description='手机号，带区号的'),
                       message_number: str = Query(
                           None, description='发送短信返回的number'),
                       message_status: int = Query(
                           None, description=SmsStatus.__doc__),
                       is_timing: int = Query(
                           None, description='不填为全部，0为即时 1为定时'),
                       country: str = Query(None, description='国家'),
                       sms_product_type: int = Query(
                           None, description=SmsProductType.__doc__),
                       created_begin_timestamp: int = Query(
                           None, description='开始创建时间'),
                       created_end_timestamp: int = Query(
                           None, description='结束创建时间'),
                       session: Session = Depends(GetSession(member_login_required))):
    """短信检查列表"""
    current_user = session.info['current_user']
    q = session.query(MessageCheck)
    q = q.filter(MessageCheck.user_id == current_user.id)

    if sms_product_type is not None or country is not None:
        q = q.filter(MessageCheck.sms_product_id == SmsProduct.id)
        if sms_product_type is not None:
            q = q.filter(SmsProduct.type.op('&')(sms_product_type))
        if country is not None:
            q = q.filter(SmsProduct.country == country)

    if phone_number is not None:
        q = q.filter(MessageCheck.phone_number == phone_number)
    if message_number is not None:
        q = q.filter(MessageCheck.message_number == message_number)
    if message_status is not None:
        q = q.filter(MessageCheck.message_status == message_status)
    if is_timing is not None:
        if is_timing:
            q = q.filter(MessageCheck.message_timing_id.isnot(None))
        else:
            q = q.filter(MessageCheck.message_timing_id.is_(None))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(MessageCheck.created_at >= timestamp_to_datetime(begin_timestamp),
                             MessageCheck.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(MessageCheck.created_at.desc())
    if export:
        headers = {
            'Content-Disposition': 'attachment; filename="messages.xlsx"'
        }
        return StreamingResponse(
            xlsx_utils.generate_xlsx_stream(
                q.all(),
                MESSAGE_CHECK_LIST_EXPORT_FIELDS),
            headers=headers)
    return q.paginate(page, per_page)


@router.get('/message_check_details/{id}', response_model=MessageCheckResponse)
def message_check_details(id: str,
                          session: Session = Depends(GetSession(member_login_required))):
    """短信检查详情"""
    current_user = session.info['current_user']
    message = session.query(MessageCheck).filter(MessageCheck.user_id == current_user.id,
                                                 MessageCheck.id == id).first()
    if not message:
        raise BsException(BsExceptionEnum.MESSAGE_CHECK_NOT_EXIST, '短信不存在')

    return message


# @router.delete('/details/{id}')
# def message_details(id: str,
#                     session: Session = Depends(GetSession(member_login_required))):
#     """删除短信"""
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


class VerifyMessageRequest(BaseModel):
    # app_id: str = Field(..., description='应用ID')

    mobile: str = Field(..., description='手机号')
    content: str = Field(None, description='短信内容,和模板二选一填写')

    # message_template_id: str = Field(None, description='短信模板ID,和内容二选一填写')

    # channel_name: str = Field(None, description='通道名称（当前版本不传）')


@router.post('/verify', response_model=MessageResponse)
def send_verify(data: VerifyMessageRequest,
                session: Session = Depends(GetSession(member_login_required))):
    """发送验证短信"""
    current_user: User = session.info['current_user']

    # app = session.query(Application).filter(Application.app_id == data.app_id).first()
    app = Application.default_get(session, current_user.id)
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    # # 优先使用用户传递进来的内容，如没传内容则必须使用模板
    # if data.content is not None:
    #     code = str(random.randint(100000, 999999))
    #     content = data.content.format(code=code)
    # elif data.message_template_id is not None:
    #     message_template = session.query(MessageTemplate).filter(
    #         MessageTemplate.id == data.message_template_id,
    #         MessageTemplate.invalid == 0,
    #         MessageTemplate.type == MessageType.NORMAL.value,
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

    code = str(random.randint(100000, 999999))
    content = data.content.format(code=code)

    try:
        mobile, price, product = SmsUser.phone_get_price_product(session, current_user, mobile,
                                                                 SmsProductType.VERIFY, None)
    except Exception as e:
        logging.error(
            'send_verify phone_get_price_product error exception: {}'.format(e))
        raise BsException(BsExceptionEnum.MOBILE_ERROR, '手机号错误')

    # 判断冻结的金额是否大于余额，是的话不允许发送
    ret = session.query(User).filter(User.id == current_user.id,
                                     User.balance > User.frozen_balance + price).update(
        dict(frozen_balance=User.frozen_balance + price))
    if ret != 1:
        raise BsException(BsExceptionEnum.BALANCE_NOT_ENOUGH, '余额不足')

    message = Message(user_id=current_user.id,
                      app_id=app.app_id,
                      type=MessageType.NORMAL.value,
                      mobile=json.dumps(data.mobile),
                      content=content,
                      status=MessageStatus.FINISH.value,
                      processed_at=datetime.datetime.now())

    session.add(message)
    session.flush()

    # sms发送接口
    sms_api = SmsApi(product.provider, product.channel.app_id,
                     product.channel.app_key)
    phone_list = [mobile]
    try:
        result_list = sms_api.send_sms_chunked(phone_list, content)
    except Exception as e:
        logging.error('messaging error exception: {}'.format(e))
        raise BsException(BsExceptionEnum.MESSAGE_SEND_ERROR, '消息发送失败')

    # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
    message_check = MessageCheck(user_id=current_user.id,
                                 message_id=message.id,
                                 sms_product_id=product.id,
                                 country=product.country,
                                 phone_number=result_list[0]['phone'],
                                 message_number=result_list[0]['id'],
                                 content=content,
                                 price=price)
    session.add(message_check)
    session.commit()

    return message


class MessageRequest(BaseModel):
    # app_id: str = Field(..., description='应用ID')

    type: MessageType = Field(..., description=MessageType.__doc__)

    group_id: int = Field(None, description='联系人组ID, 只有营销短信可以填写，和手机号二选一，手机号优先')
    mobile: List[str] = Field(None, description='手机号')

    content: str = Field(None, description='短信内容,和模板二选一填写')
    message_template_id: str = Field(None, description='短信模板ID,和内容二选一填写')

    # channel_name: str = Field(None, description='通道名称（当前版本不传）')


@router.post('/send_message', response_model=MessageResponse)
def send_message(data: MessageRequest,
                 session: Session = Depends(GetSession(member_login_required))):
    """发送普通、营销短信"""
    current_user: User = session.info['current_user']

    # app = session.query(Application).filter(Application.app_id == data.app_id).first()
    app = Application.default_get(session, current_user.id)
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')
    if len(data.mobile) > 10000:
        raise BsException(BsExceptionEnum.TOO_MANY_MOBILE, "号码过多")

    group_id = None
    # 只有营销可以用联系人组的方式来发送
    if data.type == MessageType.NORMAL:
        if data.mobile is None or len(data.mobile) == 0:
            raise BsException(BsExceptionEnum.MOBILE_NOT_EXIST, '手机号或联系人组不存在')
        mobile_list = data.mobile
    else:
        if data.mobile is not None and len(data.mobile) != 0:
            mobile_list = data.mobile
        elif data.group_id is not None:
            contact_list = session.query(Contact).filter(Contact.user_id == current_user.id,
                                                         Contact.group_id == data.group_id).all()
            if contact_list is None or len(contact_list) == 0:
                raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '联系人组不存在')
            mobile_list = [x.mobile for x in contact_list]
            group_id = data.group_id
        else:
            raise BsException(BsExceptionEnum.MOBILE_NOT_EXIST, '手机号或联系人组不存在')

    # 优先使用用户传递进来的内容，如没传内容则必须使用模板
    if data.content is not None:
        content = data.content
    elif data.message_template_id is not None:
        message_template = session.query(MessageTemplate).filter(
            MessageTemplate.id == data.message_template_id,
            MessageTemplate.type == data.type.value,
            MessageTemplate.invalid == 0,
            MessageTemplate.status == MessageTemplateStatus.SUCCESS.value).first()
        if not message_template:
            raise BsException(
                BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

        if message_template.shared == 0 and message_template.user_id != current_user.id:
            raise BsException(
                BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

        content = message_template.content
    else:
        raise BsException(BsExceptionEnum.MESSAGE_CONTENT_EMPTY, '短信内容为空')

    # 如果为使用联系人分组，则进入队列，在另外的任务中处理发送多联系人
    if group_id is not None:
        message = Message(user_id=current_user.id,
                          app_id=app.app_id,
                          group_id=group_id,
                          type=data.type.value,
                          mobile=json.dumps(mobile_list),
                          content=content)

        session.add(message)
        session.commit()
        return message

    # 如果非使用联系人分组，则进入队列，在在当前事务处理完发送后结束
    country_phone_dict = {}
    malformed_numbers = []
    for item in mobile_list:
        mobile = item

        try:
            mobile = '+{}'.format(mobile)
            number = phonenumbers.parse(mobile)
            country = phonenumbers.region_code_for_number(number)  # 可获取国家名称
            country_code = number.country_code
            mobile = number.national_number

            phone_number = '{}{}'.format(country_code, mobile)
        except Exception as e:
            malformed_numbers.append(item)
            logging.error(
                'send_message phonenumbers error exception: {}'.format(e))
            continue

        if country_phone_dict.get(country) is None:
            country_phone_dict.update({country: [phone_number]})
        else:
            country_phone_dict[country].append(phone_number)
    # if malformed_numbers:
    #     raise BsExceptionWithNumbers(BsExceptionEnum.MOBILE_ERROR,
    #                                  '手机号错误', [malformed_numbers])
    # 查找最适合的sms产品
    country_list = [country for country in country_phone_dict]
    price_product_dict = SmsUser.country_get_price_product(session, current_user, country_list,
                                                           SmsProductType.MESSAGING, None)

    amount = 0
    for country in country_phone_dict:
        phone_list = country_phone_dict[country]
        if country not in price_product_dict:
            malformed_numbers.extend(phone_list)
            continue
        amount += price_product_dict[country]['price'] * len(phone_list)
    # if malformed_numbers:
    #     raise BsExceptionWithNumbers(BsExceptionEnum.PRODUCT_NOT_EXIST, '产品未找到',
    #                                  malformed_numbers)
    # 判断冻结的金额是否大于余额，是的话不允许发送
    ret = session.query(User).filter(User.id == current_user.id,
                                     User.balance >= User.frozen_balance + amount).update(
        dict(frozen_balance=User.frozen_balance + amount))
    if ret != 1:
        raise BsException(BsExceptionEnum.BALANCE_NOT_ENOUGH, '余额不足')

    message = Message(user_id=current_user.id,
                      app_id=app.app_id,
                      group_id=group_id,
                      type=data.type.value,
                      mobile=json.dumps(mobile_list),
                      filtered_mobile=json.dumps(malformed_numbers),
                      content=content,
                      status=MessageStatus.FINISH.value,
                      processed_at=datetime.datetime.now())

    session.add(message)
    session.flush()

    for country in country_phone_dict:
        if country not in price_product_dict:
            continue
        phone_list = country_phone_dict[country]
        price = price_product_dict[country]['price']
        sms_product = price_product_dict[country]['product']

        # sms发送接口
        sms_api = SmsApi(sms_product.provider,
                         sms_product.channel.app_id, sms_product.channel.app_key)

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
                                         country=sms_product.country,
                                         sms_product_id=sms_product.id,
                                         phone_number=result_dict['phone'],
                                         message_number=result_dict['id'],
                                         content=content,
                                         price=price)
            session.add(message_check)
    session.commit()

    return message


class MessageStatisticsResponse(OrmBaseModel):
    date: str = Field(None, description='时间')
    count: int = Field(0, description='数量')


@router.get('/message_statistics', response_model=List[MessageStatisticsResponse])
def message_statistics(phone_number: str = None,
                       message_number: str = None,
                       message_status: int = None,
                       country: str = None,
                       sms_product_type: int = Query(
                           None, description=SmsProductType.__doc__),
                       created_begin_timestamp: int = None,
                       created_end_timestamp: int = None,
                       session: Session = Depends(GetSession(member_login_required))):
    """短信根据条件统计每天的数量"""
    current_user = session.info['current_user']
    time_format = '%Y-%m-%d'

    q = session.query(sa.func.date_format(
        MessageCheck.created_at, time_format), sa.func.count(MessageCheck.id))
    q = q.filter(MessageCheck.user_id == current_user.id)

    if sms_product_type is not None or country is not None:
        q = q.filter(MessageCheck.sms_product_id == SmsProduct.id)
        if sms_product_type is not None:
            q = q.filter(SmsProduct.type.op('&')(sms_product_type))
        if country is not None:
            q = q.filter(SmsProduct.country == country)

    if phone_number is not None:
        q = q.filter(MessageCheck.phone_number == phone_number)
    if message_number is not None:
        q = q.filter(MessageCheck.message_number == message_number)
    if message_status is not None:
        q = q.filter(MessageCheck.message_status == message_status)

    if created_end_timestamp is None:
        now = datetime.datetime.now()
        created_end_timestamp = datetime_to_timestamp(now)
    if created_begin_timestamp is None:
        the_date = datetime.datetime.fromtimestamp(
            created_end_timestamp) - datetime.timedelta(days=7)
        created_begin_timestamp = datetime_to_timestamp(the_date)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(MessageCheck.created_at >= timestamp_to_datetime(begin_timestamp),
                             MessageCheck.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.group_by(sa.func.date_format(
        MessageCheck.created_at, time_format)).all()

    begin_date = date_datetime(
        datetime.datetime.fromtimestamp(begin_timestamp))
    end_date = date_datetime(datetime.datetime.fromtimestamp(end_timestamp))

    date_count = [{'date': x[0], 'count': x[1]} for x in q]

    ret = []
    while begin_date <= end_date:
        find_date = False
        for item in date_count:
            if begin_date == datetime_from_str_time(item['date']):
                ret.append(item)
                find_date = True
                break
        if not find_date:
            ret.append({'date': datetime_to_str_time(begin_date), 'count': 0})
        begin_date = begin_date + datetime.timedelta(days=1)
    return ret


class SmsCountryStatisticsResponse(OrmBaseModel):
    country: str = Field(..., description='国家')
    amount: Decimal = Field(0, description='费用')
    count: int = Field(0, description='数量')


@router.get('/message_country_statistics', response_model=List[SmsCountryStatisticsResponse])
def message_country_statistics(
        sms_product_type: int = Query(
            None, description=SmsProductType.__doc__),
        message_status: int = Query(
            SmsStatus.SUCCESS, description=SmsStatus.__doc__),
        session: Session = Depends(GetSession(member_login_required))):
    """短信不同国家统计费用及数量"""
    current_user = session.info['current_user']

    q = session.query(MessageCheck.country, sa.func.sum(
        MessageCheck.price), sa.func.count(MessageCheck.id))
    q = q.filter(MessageCheck.user_id == current_user.id).filter(
        MessageCheck.message_status == message_status)
    if sms_product_type is not None:
        q = q.filter(MessageCheck.sms_product_id == SmsProduct.id)
        if sms_product_type is not None:
            q = q.filter(SmsProduct.type == sms_product_type)

    q = q.group_by(MessageCheck.country).order_by(
        sa.func.count(MessageCheck.id)).all()

    ret = [{'country': x[0], 'amount': x[1], 'count': x[2]} for x in q]
    return ret
