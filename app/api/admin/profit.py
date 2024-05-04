# -*- coding: utf-8 -*-
import logging
import time
import calendar
import sqlalchemy as sa
import decimal

from datetime import date, datetime
from app.api.member.user import verify_again
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.orm import Session

from app.api import OrmBaseModel, PaginateBase, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model import datetime_to_timestamp, timestamp_to_datetime
from app.model.admin_user import AdminUserRole, AdminUserBalanceRecordType, AdminUserBalanceRecord, AdminUser
from app.model.user import User

router = APIRouter()

q = decimal.Decimal('1.000')

def round_price(d: decimal.Decimal):
    return d.quantize(q, decimal.ROUND_DOWN)

class AdminResponse(OrmBaseModel):
    id: str
    uid: str
    role: AdminUserRole
    name: Optional[str]
    avatar: Optional[str]
    email: Optional[str]
    country_code: Optional[str]
    mobile: Optional[str]


class UserResponse(OrmBaseModel):
    id: str
    uid: str
    email: Optional[str]
    mobile: Optional[str]


# class ApplicationResponse(OrmBaseModel):
#     created_timestamp: int
#     app_id: str = Field(..., description='应用ID')
#     user_id: str = Field(..., description='用户ID')
#     name: str = Field(..., description='应用名称')
#     app_key: str = Field(..., description='应用 key')
#     secret_key: str = Field(..., description='密钥')


class ProfitRecordResponse(OrmBaseModel):
    id: int
    admin_id: str
    user_id: str
    type: str
    app_id: Optional[str]
    current_amount: Decimal
    delta_amount: Decimal
    created_timestamp: int
    record_type: AdminUserBalanceRecordType = Field(
        ..., description=AdminUserBalanceRecordType.__doc__)
    details_json: dict

    admin: Optional[AdminResponse]
    user: Optional[UserResponse]
    # application: ApplicationResponse = None


class ProfitSummaryResponse(OrmBaseModel):
    current_month: str = Field(..., description='本月收益')  # 本月收益
    sms: str = Field(..., description='本月sms收益')
    verify: str = Field(..., description='本月verify收益')
    whats_app: str = Field(..., description='本月whats_app收益')


class ProfitRecordList(PaginateBase):
    items: List[ProfitRecordResponse] = []


class ProfitAggregationRecordResponse(BaseModel):
    amount: Decimal
    timestamp: int
    day: date
    # application: ApplicationResponse = None


class ProfitAggregationList(BaseModel):
    items: List[ProfitAggregationRecordResponse]
    record_type: Optional[AdminUserBalanceRecordType] = Field(
        ..., description=AdminUserBalanceRecordType.__doc__)

class ProfitAggregationRecord2Response(BaseModel):
    amount: Decimal
    day: date
    sms: Decimal
    verify: Decimal

class ProfitAggregation2List(BaseModel):
    items: List[ProfitAggregationRecord2Response]


@router.get('/aggregation', response_model=ProfitAggregationList)
def profit_aggregation(user_id: str = None,
                       uid: str = None,
                       record_type: int = Query(None, description=AdminUserBalanceRecordType.__doc__),
                       created_begin_timestamp: int = None,
                       created_end_timestamp: int = None,
                       session: Session = Depends(
                           GetSession(admin_login_required, AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    current_user = session.info['current_user']

    # 暂时只有super可以获取其他人的数据
    if current_user.role != AdminUserRole.SUPER.value:
        user_id = current_user.id
        uid = current_user.uid

    q = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount),
                      sa.func.date(AdminUserBalanceRecord.created_at))
    if record_type is not None:
        q = q.filter(AdminUserBalanceRecord.record_type.op('&')(record_type))

    if user_id is not None:
        q = q.filter(AdminUserBalanceRecord.admin_id == user_id)
    if uid is not None:
        q = q.filter(AdminUserBalanceRecord.admin.has(
            AdminUser.uid.contains(uid)))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(AdminUserBalanceRecord.created_at >= timestamp_to_datetime(begin_timestamp),
                             AdminUserBalanceRecord.created_at < timestamp_to_datetime(end_timestamp)))
    q = q.group_by(sa.func.date(AdminUserBalanceRecord.created_at)
                   ).order_by(sa.func.date(AdminUserBalanceRecord.created_at))
    epoch = date(1970, 1, 1).toordinal()
    day_seconds = 24 * 3600
    return {
        'items': [{'amount': x[0], 'timestamp': (x[1].toordinal() - epoch) * day_seconds} for x in q],
        'record_type': record_type
    }


@router.get('/list', response_model=ProfitRecordList)
def profit_record(page: int = 1,
                  per_page: int = 5,
                  uid: str = None,
                  user_id: str = None,
                  email: str = None,
                  record_type: int = None,
                  created_begin_timestamp: int = None,
                  created_end_timestamp: int = None,
                  session: Session = Depends(
                      GetSession(admin_login_required, AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    """收益记录表"""
    current_user = session.info['current_user']

    # 暂时只有super可以获取其他人的数据
    if current_user.role != AdminUserRole.SUPER.value:
        uid = current_user.uid
        user_id = current_user.id
    else:
        if email:
            admin = session.query(AdminUser).filter(AdminUser.email == email).first()
            if admin:
                user_id = admin.id
        else:
            user_id = current_user.id

    q = session.query(AdminUserBalanceRecord)

    if record_type is not None:
        q = q.filter(AdminUserBalanceRecord.record_type.op('&')(record_type))

    # if user_id is not None:
    q = q.filter(AdminUserBalanceRecord.admin_id == user_id)

    if uid is not None:
        q = q.filter(AdminUserBalanceRecord.admin.has(
            AdminUser.uid.contains(uid)))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(AdminUserBalanceRecord.created_at >= timestamp_to_datetime(begin_timestamp),
                             AdminUserBalanceRecord.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(AdminUserBalanceRecord.id.desc())
    return q.paginate(page, per_page)


@router.get('/details/{record_id}', response_model=ProfitRecordResponse)
def profit_record_detail(record_id: int,
                         session: Session = Depends(GetSession(admin_login_required,
                                                               AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    """收益记录"""
    current_user = session.info['current_user']

    record = session.query(AdminUserBalanceRecord).filter(
        AdminUserBalanceRecord.id == record_id).first()
    if not record:
        raise BsException(BsExceptionEnum.RECORD_NOT_EXIST,
                          'Record does not exist')

    # 暂时只有super可以获取其他人的数据
    if current_user.role != AdminUserRole.SUPER.value and record.admin_id != current_user.id:
        raise BsException(BsExceptionEnum.RECORD_NOT_EXIST,
                          'Record does not exist')

    return record


@router.get('/summary', response_model=ProfitSummaryResponse)
def profit_summary(email: str = None,
                    session: Session = Depends(GetSession(admin_login_required,
                                                         AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    """收益纵览,包括当月收益/短信/验证码/Whatsapp收益"""
    current_user = session.info['current_user']

    user_id = current_user.id
    # 暂时只有super可以获取其他人的数据
    if current_user.role == AdminUserRole.SUPER.value:
        if email:
            admin = session.query(AdminUser).filter(AdminUser.email == email).first()
            if admin:
                user_id = admin.id

    q = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount)).filter(AdminUserBalanceRecord.admin_id == user_id)

    day_now = time.localtime()
    day_begin = '%d-%02d-01' % (day_now.tm_year, day_now.tm_mon)  # 月初肯定是1号
    wday, monthRange = calendar.monthrange(day_now.tm_year, day_now.tm_mon)  # 得到本月的天数 第一返回为月第一日为星期几（0-6）, 第二返回为此月天数
    day_end = '%d-%02d-%02d' % (day_now.tm_year, day_now.tm_mon, monthRange)

    q = q.filter(sa.and_(AdminUserBalanceRecord.created_at >= day_begin,
                         AdminUserBalanceRecord.created_at < day_end))

    record_sum_all = q.first()

    q1 = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount)).filter(
        AdminUserBalanceRecord.admin_id == current_user.id,
        AdminUserBalanceRecord.type == 1,
        sa.and_(
            AdminUserBalanceRecord.created_at >= day_begin,
            AdminUserBalanceRecord.created_at < day_end
        ))

    record_sum_verify = q1.first()

    q2 = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount)).filter(
        AdminUserBalanceRecord.admin_id == current_user.id,
        AdminUserBalanceRecord.type == 2,
        sa.and_(
            AdminUserBalanceRecord.created_at >= day_begin,
            AdminUserBalanceRecord.created_at < day_end
        ))

    record_sum_sms = q2.first()

    if not record_sum_all[0]:
        record_sum_all = 0
    else:
        record_sum_all = round_price(record_sum_all[0])

    if not record_sum_sms[0]:
        record_sum_sms = 0
    else:
        record_sum_sms[0] = round_price(record_sum_sms[0])

    if not record_sum_verify[0]:
        record_sum_verify = 0
    else:
        record_sum_verify = round_price(record_sum_verify[0])

    record = {
              'current_month':  record_sum_all,
              'sms': record_sum_sms,
              'verify': record_sum_verify,
              'whats_app': 0
              }

    return record


@router.get('/summary_day', response_model=ProfitAggregation2List)
def profit_aggregation(email: str = None,
                       session: Session = Depends(
                           GetSession(admin_login_required, AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    current_user = session.info['current_user']

    user_id = current_user.id
    # 暂时只有super可以获取其他人的数据
    if current_user.role == AdminUserRole.SUPER.value:
        if email:
            admin = session.query(AdminUser).filter(AdminUser.email == email).first()
            if admin:
                user_id = admin.id

    day_now = time.localtime()
    day_begin = '%d-%02d-01' % (day_now.tm_year, day_now.tm_mon)  # 月初肯定是1号
    wday, monthRange = calendar.monthrange(day_now.tm_year, day_now.tm_mon)  # 得到本月的天数 第一返回为月第一日为星期几（0-6）, 第二返回为此月天数
    day_end = '%d-%02d-%02d' % (day_now.tm_year, day_now.tm_mon, monthRange)

    q = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount),
                      sa.func.date(AdminUserBalanceRecord.created_at)).filter(
              AdminUserBalanceRecord.admin_id == user_id,
              sa.and_(
                  AdminUserBalanceRecord.created_at >= day_begin,
                  AdminUserBalanceRecord.created_at < day_end))

    q = q.group_by(sa.func.date(AdminUserBalanceRecord.created_at)
                   ).order_by(sa.func.date(AdminUserBalanceRecord.created_at))
    epoch = date(1970, 1, 1).toordinal()
    day_seconds = 24 * 3600

    arr = [{'day': '%d-%02d-%02d' % (day_now.tm_year, day_now.tm_mon, x), "amount": '0', 'sms': '0', 'verify': '0'} for x in range(1,monthRange+1)]

    for x in q:
        arr[int(x[1].strftime('%Y-%m-%d').split('-')[2]) - 1] = {
            'amount': x[0],
            'timestamp': (x[1].toordinal() - epoch) * day_seconds,
            "day": x[1].strftime('%Y-%m-%d'),
            "sms": 0,
            "verify": 0
        }

    q1 = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount),
                      sa.func.date(AdminUserBalanceRecord.created_at)).filter(
        AdminUserBalanceRecord.admin_id == user_id,
        sa.and_(
            AdminUserBalanceRecord.created_at >= day_begin,
            AdminUserBalanceRecord.created_at < day_end),
        AdminUserBalanceRecord.type == 2)

    q1 = q1.group_by(sa.func.date(AdminUserBalanceRecord.created_at)
                   ).order_by(sa.func.date(AdminUserBalanceRecord.created_at))

    for x in q1:
        arr[int(x[1].strftime('%Y-%m-%d').split('-')[2]) - 1].update({'sms': x[0]})

    q2 = session.query(sa.func.sum(AdminUserBalanceRecord.delta_amount),
                       sa.func.date(AdminUserBalanceRecord.created_at)).filter(
        AdminUserBalanceRecord.admin_id == user_id,
        sa.and_(
            AdminUserBalanceRecord.created_at >= day_begin,
            AdminUserBalanceRecord.created_at < day_end),
        AdminUserBalanceRecord.type == 1)

    q2 = q2.group_by(sa.func.date(AdminUserBalanceRecord.created_at)
                     ).order_by(sa.func.date(AdminUserBalanceRecord.created_at))

    for x in q2:
        arr[int(x[1].strftime('%Y-%m-%d').split('-')[2]) - 1].update({'verify': x[0]})

    logging.info(arr)

    record = {
        'items': arr
    }

    return record