import time
from decimal import Decimal
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import OrmBaseModel, PaginateBase, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model import timestamp_to_datetime
from app.model.user import UserBalanceType, UserBalanceRecordType, UserBalanceRecord, User
from app.model.admin_user import AdminUserRole

router = APIRouter()


class UserResponse(OrmBaseModel):
    id: str
    uid: str
    avatar: str = None
    nickname: str = None
    name: str = None
    # gender: UserGender = Field(UserGender.NOT_CHOICE, description=enum_to_json(UserGender))
    active: int
    balance: Decimal = Field(..., description='余额')
    frozen_balance: Decimal = Field(..., description='冻结余额')
    usdt_balance: Decimal = Field(..., description='usdt 金额')


class RecordResponse(OrmBaseModel):
    id: int
    current_amount: Decimal
    delta_amount: Decimal
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
                   user_id: str = None,
                   uid: str = None,
                   type: int = None,
                   record_type: int = None,
                   created_begin_timestamp: int = None,
                   created_end_timestamp: int = None,
                   session: Session = Depends(GetSession(admin_login_required))):
    """余额记录表"""
    q = session.query(UserBalanceRecord)
    if type is not None:
        q = q.filter(UserBalanceRecord.type.op('&')(type))
    if record_type is not None:
        q = q.filter(UserBalanceRecord.record_type.op('&')(record_type))

    if user_id is not None:
        q = q.filter(UserBalanceRecord.user_id == user_id)
    if uid is not None:
        q = q.filter(UserBalanceRecord.user.has(User.uid.contains(uid)))

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
                              session: Session = Depends(GetSession(admin_login_required))):
    record = session.query(UserBalanceRecord).filter(UserBalanceRecord.id == record_id).first()
    if not record:
        raise BsException(BsExceptionEnum.RECORD_NOT_EXIST, 'Record does not exist')
    return record


class RechargeRequest(BaseModel):
    uid: str = Field(..., description='用户ID')
    type: UserBalanceType = Field(..., description=UserBalanceType.__doc__)
    amount: str = Field(..., description='金额')


@router.post('/recharge', response_model=UserResponse)
def create_recharge(data: RechargeRequest,
                    session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):

    user = session.query(User).filter(User.uid == data.uid).first()
    if not user:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

    if data.type == UserBalanceType.BASE or data.type == UserBalanceType.USDT:
        user.update_balance(session,
                            data.type,
                            Decimal(data.amount),
                            UserBalanceRecordType.ADMIN_RECHARGE,
                            {'message': '管理员充值'})
    else:
        raise BsException(BsExceptionEnum.CURRENCY_NOT_EXIST, '法币类型不存在')

    session.commit()
    return user

