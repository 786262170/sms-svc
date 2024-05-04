import time
from decimal import Decimal
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import PaginateBase, BsException, BsExceptionEnum, OrmBaseModel, GetSession
from app.api.admin import admin_login_required
from app.model import timestamp_to_datetime
from app.model.user import User, UserBalanceType, UserBalanceRecordType
from app.model.admin_user import AdminUserRole

router = APIRouter()


class UserResponseAdminUser(OrmBaseModel):
    id: str
    uid: str
    avatar: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None


class UserResponse(OrmBaseModel):
    id: str
    uid: str

    created_timestamp: int = Field(..., description='创建时间')

    admin_user_id: str

    avatar: str = None
    nickname: str = None
    last_name: str = None
    first_name: str = None
    name: str = None

    active: int
    locked: int

    email: str = None
    country_code: str = None
    mobile: str = None

    # token: Optional[str]
    # level: int

    has_security_password: int

    balance: Decimal = Field(..., description='余额')
    frozen_balance: Decimal = Field(..., description='冻结余额')
    usdt_balance: Decimal = Field(..., description='余额')
    usdt_address: str = Field(None, description='usdt 充值地址')

    default_sms_channel_name: str = Field(None, description='默认通道名')
    default_verify_channel_name: str = Field(None, description='默认短信通道名')

    admin_user: Optional[UserResponseAdminUser] = None


class MemberList(PaginateBase):
    items: List[UserResponse] = []


@router.get('/list', response_model=MemberList)
def member_list(page: int = 1,
                per_page: int = 5,
                nickname: str = None,
                name: str = None,
                id: str = None,
                uid: str = None,
                admin_user_id: str = None,
                email: str = None,
                mobile: str = None,
                # level: int = None,
                locked: int = None,
                active: int = None,
                created_begin_timestamp: int = None,
                created_end_timestamp: int = None,
                session: Session = Depends(GetSession(admin_login_required,
                                                      AdminUserRole.FINANCE |
                                                      AdminUserRole.ALL_AGENT |
                                                      AdminUserRole.CSR))):
    """用户列表"""
    current_user = session.info['current_user']

    q = session.query(User)
    if id is not None:
        q = q.filter(User.id == id)
    if uid is not None:
        q = q.filter(User.uid == uid)
    if admin_user_id is not None:
        q = q.filter(User.admin_user_id == admin_user_id)
    if nickname is not None:
        q = q.filter(User.nickname == nickname)
    if name is not None:
        q = q.filter(User.name == name)
    if email is not None:
        q = q.filter(User.email == email)
    if mobile is not None:
        q = q.filter(User.mobile == mobile)
    # if level is not None:
    #     q = q.filter(User.level == level)
    if locked is not None:
        q = q.filter(User.locked == locked)
    if active is not None:
        q = q.filter(User.active == active)

    # 暂时只有super可以获取所有人，其他角色只能查自己
    if current_user.role != AdminUserRole.SUPER.value:
        q = q.filter(User.admin_user_id == current_user.id)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(User.created_at >= timestamp_to_datetime(begin_timestamp),
                             User.created_at < timestamp_to_datetime(end_timestamp)))
    q = q.order_by(User.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/details/{member_id}', response_model=UserResponse)
def get_member_detail(member_id: str,
                      session: Session = Depends(GetSession(admin_login_required,
                                                            AdminUserRole.FINANCE |
                                                            AdminUserRole.ALL_AGENT |
                                                            AdminUserRole.CSR))):
    """用户详情"""
    current_user = session.info['current_user']

    # 暂时只有super可以获取所有人，其他角色只能查自己
    if current_user.role != AdminUserRole.SUPER.value:
        user = session.query(User).filter(
            User.id == member_id, User.admin_user_id == current_user.id).first()
    else:
        user = session.query(User).filter(User.id == member_id).first()

    if not user:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')
    return user


class MemberRequest(BaseModel):
    password: str = None
    security_password: str = None
    locked: int = None
    active: int = None
    default_sms_channel_name: str = Field(None, description='默认通道名。设置为 auto 则自动选择。')
    default_verify_channel_name: str = Field(None, description='默认验证码通道名。设置为 auto 则自动选择')
    # usdt_amount: Decimal = None


@router.put('/details/{member_id}', response_model=UserResponse)
def modify_member_detail(member_id: str,
                         data: MemberRequest,
                         session: Session = Depends(GetSession(admin_login_required,
                                                               AdminUserRole.FINANCE | AdminUserRole.ALL_AGENT))):
    """修改用户信息"""
    user = session.query(User).filter(User.id == member_id).first()
    if not user:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

    if data.password:
        user.set_password(data.password)
    if data.security_password:
        user.set_security_password(data.security_password)
    if data.locked is not None:
        user.locked = data.locked
    if data.active is not None:
        user.active = data.active
    # if data.default_sms_channel_name is not None:
    #     user.default_sms_channel_name = None if data.default_sms_channel_name == 'auto' else data.default_sms_channel_name
    # if data.default_verify_channel_name is not None:
    #     user.default_verify_channel_name = None if data.default_verify_channel_name == 'auto' else data.default_verify_channel_name
    # if data.usdt_amount is not None:
    user.default_sms_channel_name = data.default_sms_channel_name
    user.default_verify_channel_name = data.default_verify_channel_name
    #     user.update_balance(session,
    #                         UserBalanceType.USDT,
    #                         data.usdt_amount,
    #                         UserBalanceRecordType.ADMIN_RECHARGE,
    #                         {'message': '管理员充值'})
    session.commit()
    return user
