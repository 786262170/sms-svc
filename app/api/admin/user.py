import json

from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response
from pydantic import BaseModel, Field

from app.api import BsException, BsExceptionEnum, PaginateBase, GetSession, OrmBaseModel
from app.api.admin import admin_login_required
from app.model.admin_user import AdminUser, AdminUserRole
from app.model.pin_code import CaptchaPinCode, EmailPinCode

router = APIRouter()


class AdminLoginRequest(BaseModel):
    uid: str
    password: str
    uuid: str
    captcha_pin_code: str


class AdminUserResponse(OrmBaseModel):
    id: str
    uid: str
    locked: int
    role: AdminUserRole
    created_timestamp: int
    email: str
    country_code: str = None
    mobile: str = None
    avatar: str = None
    name: str = None
    permission_json: dict = None
    code: str = None
    has_security_password: int
    balance: Decimal = Field(..., description='余额')


class LoginAdminUserResponse(AdminUserResponse):
    token: str


@router.post("/login", response_model=LoginAdminUserResponse)
def admin_login(response: Response,
                data: AdminLoginRequest,
                session: Session = Depends(GetSession())):
    """管理员登录"""
    admin_user = session.query(AdminUser).filter_by(uid=data.uid).first()
    if not admin_user:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'uid does not exist')
    CaptchaPinCode.flask_check(session, data.uuid, data.captcha_pin_code)

    if admin_user.verify_password(data.password):
        admin_user.generate_auth_token()
        if admin_user.locked:
            raise BsException(BsExceptionEnum.USER_LOCKED, '用户已被锁定')

        if not admin_user.active:
            raise BsException(BsExceptionEnum.USER_NOT_ACTIVE, '用户未激活')

        response.set_cookie(key='token',
                            value=str(admin_user.token, encoding='utf-8'),
                            samesite='None',
                            secure=True,
                            max_age=(60 * 60 * 24 * 365))
        session.commit()
        return admin_user
    else:
        raise BsException(BsExceptionEnum.PASSWORD_NOT_MATCH,
                          'password does not match')


@router.post("/logout")
def admin_login(response: Response,
                session: Session = Depends(GetSession(admin_login_required))):
    """管理员退出登录"""
    current_user = session.info['current_user']
    current_user.generate_auth_token()
    session.commit()
    response.set_cookie(key='token', max_age=0)
    return {}


class AdminResetPasswordRequest(BaseModel):
    password: str
    new_password: str


@router.post("/reset_password", response_model=AdminUserResponse)
def admin_reset_password(data: AdminResetPasswordRequest,
                         session: Session = Depends(GetSession(admin_login_required))):
    """重置密码"""
    current_user = session.info['current_user']
    if not current_user.verify_password(data.password):
        raise BsException(BsExceptionEnum.PASSWORD_NOT_MATCH,
                          'password does not match')
    current_user.set_password(data.new_password)
    current_user.generate_auth_token()
    session.commit()
    return current_user


class RegisterRequest(BaseModel):
    uid: str
    name: str = None
    email: str
    pin_code: str
    password: str
    country_code: str = None
    mobile: str = None
    code: str = None
    permission: dict = None


@router.post('/register', response_model=AdminUserResponse)
def register_admin_user(data: RegisterRequest,
                        session: Session = Depends(GetSession())):
    """管理员注册"""
    data.email = data.email.lower().strip()
    admin_user = session.query(AdminUser).filter(
        AdminUser.uid == data.uid).first()
    if admin_user:
        raise BsException(BsExceptionEnum.USER_UID_EXIST,
                          'admin uid does exist')
    admin_user = session.query(AdminUser).filter(
        AdminUser.email == data.email).first()
    if admin_user:
        raise BsException(BsExceptionEnum.EMAIL_EXIST,
                          'admin email exists')
    if data.code is None:
        sponsor = session.query(AdminUser).get(AdminUser.ROOT_ID)
    else:
        # 暂时只有super可以推荐代理，后续有多级代理再进行修改
        sponsor = session.query(AdminUser).filter(
            AdminUser.code == data.code).first()
    if sponsor is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST,
                          'sponsor uid does not exist')

    EmailPinCode.flask_check(
        session, data.email, data.pin_code)  # todo 调试暂时取消邮箱验证

    admin_user = AdminUser(uid=data.uid,
                           name=data.name,
                           parent_id=sponsor.id,
                           role=AdminUserRole.FIRST_AGENT.value,
                           email=data.email,
                           permission=json.dumps(data.permission))
    admin_user.set_password(data.password)
    session.add(admin_user)
    session.flush()
    admin_user.set_code()
    admin_user.activate(session)
    session.commit()
    return admin_user


@router.get('/current_user', response_model=AdminUserResponse)
def get_current_user(current_user=Depends(admin_login_required)):
    return current_user


class AdminUserList(PaginateBase):
    items: List[AdminUserResponse] = []


@router.get('/list', response_model=AdminUserList)
def admin_list(page: int = 1,
               per_page: int = 5,
               role: int = 0,
               locked: int = 0,
               email: str = None,
               name: str = None,
               parent_id: str = None,
               session: Session = Depends(GetSession(admin_login_required, AdminUserRole.ALL_ROLE))):  # 如后续支持代理，要添加role
    """管理员列表"""
    current_user = session.info['current_user']

    # 暂时只有super可以获取其他人
    # if current_user.role != AdminUserRole.SUPER.value:
    #     parent_id = current_user.id

    q = session.query(AdminUser)
    q = q.filter(AdminUser.id.in_(AdminUser.team_id(session, current_user)))
    q = q.filter(AdminUser.id != current_user.id)

    if current_user.role == AdminUserRole.SUPER:
        q = q.filter(AdminUser.role != AdminUserRole.SUPER)
        if role:
            q = q.filter(AdminUser.role == role)
    elif role:
        q = q.filter(AdminUser.role == role)

    if locked:
        q = q.filter(AdminUser.locked == locked)
    if email:
        q = q.filter(AdminUser.email == email)
    if name:
        q = q.filter(AdminUser.name == name)
    if parent_id:
        q = q.filter(AdminUser.parent_id == parent_id)
    q = q.order_by(AdminUser.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/details/{id}', response_model=AdminUserResponse)
def admin_detail(admin_id: str,
                 session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):  # 如后续支持代理，要添加role
    """管理员信息"""
    current_user = session.info['current_user']

    # 暂时只有super可以获取其他人
    if current_user.role != AdminUserRole.SUPER.value:
        admin_user = session.query(AdminUser).filter(
            AdminUser.id == admin_id).first()
    else:
        parent_id = current_user.id
        admin_user = session.query(AdminUser).filter(
            AdminUser.id == admin_id, AdminUser.parent_id == parent_id).first()
    if not admin_user:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST,
                          'admin id does exist')
    return admin_user


class ModifyAdminRequest(BaseModel):
    uid: str = None
    new_password: str = None
    old_password: str = None
    new_security_password: str = None
    old_security_password: str = None
    name: str = None
    avatar: str = None
    country_code: str = None
    mobile: str = None
    permission: dict = None
    locked: int = None


@router.put('/details', response_model=AdminUserResponse)
def modify_admin_detail(data: ModifyAdminRequest,
                        session: Session = Depends(GetSession(admin_login_required))):
    current_user = session.info['current_user']

    # 暂时只有super可以直接修改其他用户的信息，其他个人只能修改自己
    if current_user.role == AdminUserRole.SUPER.value:

        if data.uid is None:
            raise BsException(BsExceptionEnum.USER_NOT_EXIST, '管理员UID不存在')

        admin_user = session.query(AdminUser).filter(
            AdminUser.uid == data.uid).first()
        if not admin_user:
            raise BsException(BsExceptionEnum.USER_NOT_EXIST, '管理员不存在')

        if data.new_password is not None:
            admin_user.set_password(data.new_password)
        if data.permission is not None:
            admin_user.permission = json.dumps(data.permission)
        if data.locked is not None:
            admin_user.locked = data.locked
    else:
        if data.new_password and data.old_password:
            if not current_user.verify_password(data.old_password):
                raise BsException(
                    BsExceptionEnum.PASSWORD_NOT_MATCH, 'old_password does not match')
            current_user.set_password(data.new_password)
        if current_user.has_security_password:
            if data.new_security_password and data.old_security_password:
                if not current_user.verify_security_password(data.old_security_password):
                    raise BsException(
                        BsExceptionEnum.PASSWORD_NOT_MATCH, 'old_security_password does not match')
                current_user.set_security_password(data.new_security_password)
        else:
            if data.new_security_password:
                current_user.set_security_password(data.new_security_password)

            if data.avatar:
                current_user.avatar = data.avatar
            if data.name:
                current_user.name = data.name
            if data.country_code:
                current_user.country_code = data.country_code
            if data.mobile:
                current_user.mobile = data.mobile

        admin_user = current_user

    session.commit()
    return admin_user
