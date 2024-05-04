# -*- coding: utf-8 -*-
from app.utils.email import send_mail_with_template
import binascii
import json
import random
import time
import uuid
from decimal import Decimal
from typing import List

import requests
import sqlalchemy as sa
from app.api import (BsException, BsExceptionEnum, GetSession, OrmBaseModel,
                     PaginateBase, app_config, get_db)
from app.api.admin import AdminUser
from app.api.member import (member_login_required,
                            member_not_verify_again_required)
from app.model import timestamp_to_datetime
from app.model.pin_code import CaptchaPinCode, EmailPinCode, SmsPinCode
from app.model.user import User, UserLoginRecord
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from starlette.responses import Response, StreamingResponse

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str = Field(None, description='first_name')
    last_name: str = Field(None, description='last_name')
    # admin_user_id: str
    # admin_uid: str
    code: str = Field(None, description='推荐码')


class UserResponse(OrmBaseModel):
    id: str = Field(..., description='用户ID')
    uid: str = Field(..., description='用户UID，易记的短唯一码')

    # admin_user_id: str = Field(..., description='管理员ID')

    avatar: str = Field(None, description='头像')
    # nickname: str = Field(None, description='昵称')
    # name: str = Field(None, description='姓名')
    first_name: str = Field(None, description='first_name')
    last_name: str = Field(None, description='last_name')

    email: str
    # country_code: str = Field(None, description='手机区号')
    mobile: str = Field(None, description='手机号')
    token: str = Field(None, description='令牌')
    # level: int
    active: int = Field(..., description='激活状态')

    status_2FA: int = Field(..., description='2次验证状态 0 关闭  1开启')

    # has_security_password: int = Field(..., description='是否有安全密码')

    balance: Decimal = Field(..., description='余额')
    frozen_balance: Decimal = Field(..., description='冻结余额')
    usdt_balance: Decimal = Field(..., description='USDT余额')
    usdt_address: str = Field(None, description='usdt 充值地址')

class LoginUserResponse(UserResponse):
    token: str

@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest,
             session: Session = Depends(get_db)):
    """用户注册"""
    # admin_user = session.query(AdminUser).filter(AdminUser.id == data.admin_user_id).first()
    # admin_user = session.query(AdminUser).filter(AdminUser.uid == data.admin_uid).first()
    if data.code is None:
        admin_user = session.query(AdminUser).get(AdminUser.ROOT_ID)
    else:
        admin_user = session.query(AdminUser).filter(
            AdminUser.code == data.code).first()
    if admin_user is None:
        raise BsException(BsExceptionEnum.SPONSOR_CODE_NOT_EXIST, '推荐码不存在')

    user = session.query(User).filter(User.email == data.email).first()

    if user is not None and user.active == 1:
        raise BsException(BsExceptionEnum.EMAIL_EXIST, '邮箱已存在')

    if not user:
        user = User()
        session.add(user)

    user.email = data.email
    user.last_name = data.last_name
    user.first_name = data.first_name
    user.admin_user_id = admin_user.id
    user.set_uid(session)
    user.set_password(data.password)
    session.flush()

    code = str(random.randint(100000, 999999))
    pin_code = session.query(EmailPinCode).get(data.email)
    if pin_code is None:
        pin_code = EmailPinCode(id=data.email)
    pin_code.generate_signature(session, code)  # 有效期48小时

    try:
        send_mail_with_template(data.email,
            app_config.EMAIL_ACTIVE_MAIL_TITLE,
            app_config.EMAIL_ACTIVE_TEMPLATE,
            {
                'link': app_config.EMAIL_ACTIVE_ACCOUNT.format(email=data.email, code=code)
            })
    except Exception as e:
        raise BsException(BsExceptionEnum.EMAIL_SEND_ERROR, {'msg': e.message})

    # user.generate_auth_token()
    session.commit()
    return user


class LoginRequest(BaseModel):
    email: str
    # name: str = None
    password: str
    uuid: str = Field(..., description='图形验证码请求的ID')
    captcha_pin_code: str = Field(..., description='图形验证码')
    # sms_pin_code: str = Field(None, description='短信验证码（开启二次验证才需要）')


@router.post("/login", response_model=LoginUserResponse)
def login(response: Response,
          data: LoginRequest,
          session: Session = Depends(get_db)):
    """用户登录"""
    if data.email:
        user = session.query(User).filter(User.email == data.email).first()
        if user is None:
            raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

        if not user.verify_password(data.password):
            raise BsException(BsExceptionEnum.PASSWORD_NOT_MATCH, '密码错误')
    else:
        raise BsException(BsExceptionEnum.PARAMETER_ERROR, '请选择一种登录')

    CaptchaPinCode.flask_check(session, data.uuid, data.captcha_pin_code)

    if user.status_2FA:
        user.generate_auth_token(verify_again=True)
    else:
        user.generate_auth_token()
        # if data.sms_pin_code is None:
        #     raise BsException(BsExceptionEnum.SMS_PIN_CODE_NOT_MATCH, '手机验证码不匹配')
        # SmsPinCode.flask_check(session, user.mobile, data.sms_pin_code)

    if user.locked:
        raise BsException(BsExceptionEnum.USER_LOCKED, '用户已被锁定')

    if not user.active:
        raise BsException(BsExceptionEnum.USER_NOT_ACTIVE, '用户未激活')

    if not user.status_2FA:
        login_record = UserLoginRecord(user_id=user.id, login_status=1)
        session.add(login_record)

    # todo 调试时打开，正式关闭
    response.set_cookie(key='token',
                        value=str(user.token, encoding='utf-8'),
                        samesite='None',
                        secure=True,
                        max_age=(60 * 60 * 24 * 365))
    session.commit()
    return user


class VerifyAgainRequest(BaseModel):
    sms_pin_code: str = Field(None, description='短信验证码')


@router.post("/verify_again", response_model=UserResponse)
def verify_again(response: Response,
                 data: VerifyAgainRequest,
                 session: Session = Depends(get_db),
                 current_user=Depends(member_not_verify_again_required)):
    SmsPinCode.flask_check(session, current_user.mobile, data.sms_pin_code)
    current_user.generate_auth_token(False)
    login_record = UserLoginRecord(user_id=current_user.id, login_status=1)
    session.add(login_record)
    response.set_cookie(key='token', value=str(
        current_user.token, encoding='utf-8'), max_age=(60 * 60 * 24 * 365))
    session.commit()
    return current_user


@router.post('/logout')
def logout(response: Response,
           session: Session = Depends(get_db),
           current_user=Depends(member_login_required)):
    """退出"""
    current_user.generate_auth_token()

    login_record = UserLoginRecord(user_id=current_user.id, login_status=0)
    session.add(login_record)

    session.commit()
    response.set_cookie(key='token', max_age=0)
    return {}


class UserActiveRequest(BaseModel):
    pin_code: str = Field(..., description='邮件验证码')


@router.put('/active/{email}', response_model=UserResponse)
def active(email: str,
           data: UserActiveRequest,
           session: Session = Depends(get_db)):
    """用户激活"""

    EmailPinCode.flask_check(session, email, data.pin_code)
    user = session.query(User).filter(User.email == email,
                                      User.active == 0,
                                      User.locked == 0).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')

    user.activate(session)

    session.commit()
    return user


class UserGetBackPasswordRequest(BaseModel):
    email: str


@router.post('/get_back_password')
def get_back_password(data: UserGetBackPasswordRequest,
                      session: Session = Depends(get_db)):
    """找回密码"""
    user = session.query(User).filter(User.email == data.email,
                                      User.active == 1,
                                      User.locked == 0).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')

    code = str(random.randint(100000, 999999))
    pin_code = session.query(EmailPinCode).get(data.email)
    if pin_code is None:
        pin_code = EmailPinCode(id=data.email)
    pin_code.generate_signature(session, code)  # 有效期48小时

    try:
        send_mail_with_template(
            data.email,
            app_config.EMAIL_RESET_PASSWORD_TITLE,
            app_config.EMAIL_RESET_PASSWORD_TEMPLATE,
            {
                'link': app_config.EMAIL_RESET_PASSWORD.format(email=data.email, code=code)
            }
        )
    except Exception as e:
        raise BsException(BsExceptionEnum.EMAIL_SEND_ERROR, {'msg': e.message})

    return {}


class UserResetPasswordRequest(BaseModel):
    pin_code: str = Field(..., description='邮件验证码')
    new_password: str


@router.put('/reset_password/{email}')
def reset_password(email: str,
                   data: UserResetPasswordRequest,
                   session: Session = Depends(get_db)):
    """重置密码"""
    user = session.query(User).filter(User.email == email,
                                      User.active == 1,
                                      User.locked == 0).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')

    EmailPinCode.flask_check(session, email, data.pin_code)

    user.set_password(data.new_password)

    session.commit()
    return {}


@router.get('/current_user', response_model=UserResponse)
def get_current_user(current_user=Depends(member_login_required)):
    return current_user


class CurrentUserRequest(BaseModel):
    first_name: str = Field(None, description='first_name（修改传值，不修改不传）')
    last_name: str = Field(None, description='last_name（修改传值，不修改不传）')
    status_2FA: int = Field(None, description='更改是否开启二次验证（修改传值，不修改不传）')
    # nickname: str = Field(None, description='昵称')
    # name: str = Field(None, description='姓名')
    # avatar: str = Field(None, description='头像')
    # country_code: str = Field(None, description='手机区号')
    # mobile: str = Field(None, description='手机号')
    old_password: str = None
    new_password: str = None
    # old_security_password: str = None
    # new_security_password: str = None


@router.put('/current_user', response_model=UserResponse)
def put_current_user(data: CurrentUserRequest,
                     session: Session = Depends(get_db),
                     current_user: User = Depends(member_login_required)):
    """更改个人信息(包括修改密码)"""
    if data.new_password and data.old_password:
        if not current_user.verify_password(data.old_password):
            raise BsException(BsExceptionEnum.PASSWORD_NOT_MATCH,
                              'old_password does not match')
        current_user.set_password(data.new_password)

    if data.status_2FA and current_user.mobile:
        current_user.status_2FA = 1
    else:
        current_user.status_2FA = 0

    if data.first_name:
        current_user.first_name = data.first_name
    if data.last_name:
        current_user.last_name = data.last_name

    session.commit()
    return current_user


class User2FARequest(BaseModel):
    # country_code: str = Field(..., description='手机区号')
    mobile: str = Field(..., description='手机号')
    sms_pin_code: str = Field(..., description='手机验证码')


@router.put('/bind_2fa', response_model=UserResponse)
def bind_2fa(data: User2FARequest,
             session: Session = Depends(get_db),
             current_user: User = Depends(member_login_required)):
    """绑定2次校验"""

    SmsPinCode.flask_check(session, data.mobile, data.sms_pin_code)

    current_user.mobile = data.mobile
    current_user.status_2FA = 1

    session.commit()
    return current_user


# class UserModify2FARequest(BaseModel):
#     status_2FA: int = Field(..., description='2次验证状态')
#
#
# @router.put('/modify_2fa', response_model=UserResponse)
# def modify_2fa(data: UserModify2FARequest,
#                session: Session = Depends(get_db),
#                current_user: User = Depends(member_login_required)):
#     """打开关闭2次校验"""
#     if data.status_2FA:
#         current_user.status_2FA = 1
#     else:
#         current_user.status_2FA = 0
#
#     session.commit()
#     return current_user


# class Status2FAResponse(OrmBaseModel):
#     status_2FA: int = Field(..., description='2次验证状态')
#
#
# @router.get('/status_2fa/{email}', response_model=Status2FAResponse)
# def status_2fa(email: str,
#                session: Session = Depends(get_db)):
#     """是否开启2次校验"""
#     user = session.query(User).filter(User.email == email,
#                                       User.active == 1,
#                                       User.locked == 0).first()
#     if user is None:
#         raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')
#
#     return user


class LoginRecordResponse(OrmBaseModel):
    created_timestamp: int = Field(..., description='创建时间')

    # user_id: str = Field(..., description='用户ID')

    login_status: int = Field(..., description='登录状态')


class LoginRecordList(PaginateBase):
    items: List[LoginRecordResponse] = []


@router.get('/login_record_list', response_model=LoginRecordList)
def login_record_list(page: int = 1,
                      per_page: int = 5,
                      login_status: int = None,
                      created_begin_timestamp: int = None,
                      created_end_timestamp: int = None,
                      session: Session = Depends(GetSession(member_login_required))):
    """登录记录列表"""
    current_user = session.info['current_user']
    q = session.query(UserLoginRecord)
    q = q.filter(UserLoginRecord.user_id == current_user.id)
    if login_status is not None:
        q = q.filter(UserLoginRecord.login_status == login_status)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(UserLoginRecord.created_at >= timestamp_to_datetime(begin_timestamp),
                             UserLoginRecord.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(UserLoginRecord.created_at.desc())
    return q.paginate(page, per_page)


@router.get("/api_doc", response_description='pdf')
async def api_doc():
    """下载联系人模板"""
    f = open("doc/icaicloud-sms接口文档.pdf", "br")

    headers = {
        'Content-Disposition': 'attachment; filename="icaicloud-sms.pdf"'
    }
    return StreamingResponse(f, headers=headers)
