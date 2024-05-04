# -*- coding: utf-8 -*-
from typing import List
from decimal import Decimal

import time
import requests
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import PaginateBase, OrmBaseModel, get_db, BsException, BsExceptionEnum, GetSession, app_config
from app.api.member import member_login_required
from app.model import timestamp_to_datetime
from app.model.user import UserBalanceType, UserBalanceRecord, UserBalanceRecordType, User
from app.model.setting import Setting

router = APIRouter()


class UserResponse(OrmBaseModel):
    id: str
    uid: str
    avatar: str = None
    nickname: str = None
    name: str = None
    # gender: UserGender = Field(UserGender.NOT_CHOICE, description=enum_to_json(UserGender))
    active: int
    # usdt_balance: Decimal = Field(..., description='usdt 金额')


class RecordResponse(OrmBaseModel):
    id: int
    current_amount: Decimal = Field(..., description='当前金额')
    delta_amount: Decimal = Field(..., description='变化金额')
    created_timestamp: int
    record_type: UserBalanceRecordType = Field(..., description=UserBalanceRecordType.__doc__)
    type: UserBalanceType = Field(..., description=UserBalanceType.__doc__)
    details_json: dict

    user: UserResponse
    other_user: UserResponse = None


class RecordList(PaginateBase):
    items: List[RecordResponse] = []


@router.get('/list', response_model=RecordList)
def balance_record(page: int = 1,
                   per_page: int = 5,
                   type: int = None,
                   record_type: int = None,
                   is_income: bool = None,
                   created_begin_timestamp: int = None,
                   created_end_timestamp: int = None,
                   current_user=Depends(member_login_required),
                   session: Session = Depends(get_db)):
    """余额记录表"""
    q = session.query(UserBalanceRecord)
    q = q.filter(UserBalanceRecord.user_id == current_user.id)
    if type is not None:
        q = q.filter(UserBalanceRecord.type.op('&')(type))
    if record_type is not None:
        q = q.filter(UserBalanceRecord.record_type.op('&')(record_type))
    if is_income is not None:
        if is_income:
            q = q.filter(UserBalanceRecord.delta_amount > 0)
        else:
            q = q.filter(UserBalanceRecord.delta_amount < 0)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(UserBalanceRecord.created_at >= timestamp_to_datetime(begin_timestamp),
                             UserBalanceRecord.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(UserBalanceRecord.id.desc())
    return q.paginate(page, per_page)


@router.get('/details/{record_id}', response_model=RecordResponse)
def get_balance_record_detail(record_id: int,
                              session: Session = Depends(GetSession(member_login_required))):
    current_user = session.info['current_user']
    record = session.query(UserBalanceRecord).filter(UserBalanceRecord.id == record_id,
                                                     UserBalanceRecord.user_id == current_user.id).first()
    if not record:
        raise BsException(BsExceptionEnum.RECORD_NOT_EXIST, 'Record does not exist')
    return record

# @router.get('/total_record', response_model=RecordList)
# def balance_total_record(page: int = 1,
#                          per_page: int = 5,
#                          type: int = None,
#                          record_type: int = None,
#                          is_income: bool = None,
#                          created_begin_timestamp: int = None,
#                          created_end_timestamp: int = None,
#                          current_user=Depends(member_login_required),
#                          session: Session = Depends(get_db)):
#     """余额记录表"""
#     q = session.query(UserBalanceRecord)
#     if type is not None:
#         q = q.filter(UserBalanceRecord.type.op('&')(type))
#     if record_type is not None:
#         q = q.filter(UserBalanceRecord.record_type.op('&')(record_type))
#     if is_income is not None:
#         if is_income:
#             q = q.filter(UserBalanceRecord.delta_amount > 0)
#         else:
#             q = q.filter(UserBalanceRecord.delta_amount < 0)
#
#     if created_begin_timestamp:
#         if not created_end_timestamp:
#             created_end_timestamp = int(time.time())
#         begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
#         end_timestamp = max(created_begin_timestamp, created_end_timestamp)
#         q = q.filter(sa.and_(UserBalanceRecord.created_at >= timestamp_to_datetime(begin_timestamp),
#                              UserBalanceRecord.created_at < timestamp_to_datetime(end_timestamp)))
#
#     q = q.order_by(UserBalanceRecord.id.desc())
#     return q.paginate(page, per_page)


class RechargeRequest(BaseModel):
    number: str
    currency_code: str
    erc20_token: int
    amount: str
    paid_amount: str
    delta_amount: str
    extra: str
    status: int
    signature: str


@router.post('/recharge')
def create_recharge(data: RechargeRequest,
                    session: Session = Depends(get_db)):
    User.check_sign(data.dict(), app_config.APP_ID, app_config.APP_KEY)

    setting = Setting.get_json(session, 'general_option')

    recharge_fee_rate = Decimal(setting['recharge_fee_rate']) / 100

    r = requests.post(app_config.DIZPAY_QUERY_CURRENCY, json=dict(currency_list='CNY'))

    if r.status_code == requests.codes.ok:
        if r.encoding is None or r.encoding == 'ISO-8859-1':
            r.encoding = 'UTF-8'
        usd2cny_rate = Decimal(r.json().get('objects')[0]['usd_rate'])
    else:
        raise BsException(BsExceptionEnum.CURRENCY_NOT_EXIST, r.text)

    if data.currency_code == 'USDT':
        user = session.query(User).filter(User.usdt_number == data.number).first()

        if user is None:
            raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

        session.query(User).filter(User.usdt_number == data.number).update(dict(
            usdt_recharge=User.usdt_recharge + Decimal(data.delta_amount)
        ))
        session.flush()
        if user.usdt_recharge > Decimal(data.paid_amount):
            return {}

        user.update_balance(session,
                            UserBalanceType.USDT,
                            Decimal(data.delta_amount) * usd2cny_rate * (1 - recharge_fee_rate),
                            UserBalanceRecordType.RECHARGE,
                            {'message': '用户充值'})

    # elif data.currency_code == 'MTN':
    #     user = session.query(User).filter(User.token_number == data.number).first()
    #
    #     if user is None:
    #         raise BsException(BsExceptionEnum.UID_NOT_EXIST, '用户不存在')
    #
    #     session.query(User).filter(User.token_number == data.number).update(dict(
    #         token_recharge=User.token_recharge + Decimal(data.delta_amount)
    #     ))
    #     session.flush()
    #     if user.token_recharge > Decimal(data.paid_amount):
    #         return {}
    #     user.update_balance(session,
    #                         UserBalanceType.TOKEN,
    #                         Decimal(data.delta_amount),
    #                         UserBalanceRecordType.RECHARGE)

    else:
        raise BsException(BsExceptionEnum.CURRENCY_NOT_EXIST, '法币类型不存在')

    session.commit()
    return {}

