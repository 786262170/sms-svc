# -*- coding: utf-8 -*-
import time
from typing import List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model import timestamp_to_datetime
from app.model.application import Application, ApplicationCategory
from app.model.admin_user import AdminUserRole
from app.model.user import User

router = APIRouter()


class ApplicationResponse(OrmBaseModel):
    created_timestamp: int
    app_id: str = Field(..., description='应用ID')
    user_id: str = Field(..., description='用户ID')
    name: str = Field(..., description='应用名称')
    app_key: str = Field(..., description='应用 key')
    # secret_key: str = Field(..., description='密钥')
    sms_hook_url: str = Field(None, description='sms失败回调的 url')
    invalid: int = Field(..., description='无效')
    country: Optional[str] = Field(..., description='国家')
    link: Optional[str] = Field(..., description='GP链接')
    remark: Optional[str] = Field(..., description='备注')
    category: ApplicationCategory


class ApplicationList(PaginateBase):
    items: List[ApplicationResponse] = []


@router.get('/list', response_model=ApplicationList)
def application_list(page: int = 1,
                     per_page: int = 5,
                     user_id: str = None,
                     invalid: int = 0,
                     created_begin_timestamp: int = None,
                     created_end_timestamp: int = None,
                     session: Session = Depends(GetSession(admin_login_required))):
    """应用列表"""
    q = session.query(Application)
    if user_id is not None:
        q = q.filter(Application.user_id == user_id)
    q = q.filter(Application.invalid == invalid)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(Application.created_at >= timestamp_to_datetime(begin_timestamp),
                             Application.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(Application.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/details/{app_id}', response_model=ApplicationResponse)
def application_details(app_id: str,
                        session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """应用详情"""
    app = session.query(Application).filter(Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    return app


@router.delete('/details/{app_id}')
def application_details(app_id: str,
                        session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """删除应用"""
    app = session.query(Application).filter(Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    # session.delete(app)
    app.invalid = 1
    session.commit()

    return {}


class ApplicationRequest(BaseModel):
    user_id: str = Field(None, description='用户ID')
    name: str = Field(None, description='应用名称')
    sms_hook_url: str = Field(None, description='应用名称')
    country: str = Field(None, description='国家')
    link: str = Field(None, description='GP链接')
    remark: str = Field(None, description='备注')
    category: ApplicationCategory  = Field(None, description=ApplicationCategory.__doc__)


@router.post('/create', response_model=ApplicationResponse)
def create_application(data: ApplicationRequest,
                       session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """添加应用"""
    if data.user_id is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户ID不存在')

    user = session.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

    if data.name is None:
        raise BsException(BsExceptionEnum.APP_NAME_NOT_EXIST, '应用名称不存在')

    app = Application(name = data.name, user_id=data.user_id,  _app_key=Application.generate_app_key())
   
    # 新增其他可选参数
    if data.sms_hook_url is not None:
        app.sms_hook_url = data.sms_hook_url

    if data.link is not None:
        app.link = data.link

    if data.category is not None:
        app.category = data.category.value

    if data.remark is not None:
        app.remark = data.remark

    if data.country is not None:
        app.country = data.country

    app.set_app_id(session)
    session.add(app)
    session.flush()
    session.commit()

    return app


@router.put('/details/{app_id}', response_model=ApplicationResponse)
def modify_application(app_id: str,
                       data: ApplicationRequest,
                       session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """修改应用"""
    app = session.query(Application).filter(Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    if data.name is not None:
        app.name = data.name

    if data.sms_hook_url is not None:
        app.sms_hook_url = data.sms_hook_url

    if data.link is not None:
        app.link = data.link

    if data.category is not None:
        app.category = data.category.value

    if data.remark is not None:
        app.remark = data.remark

    if data.country is not None:
        app.country = data.country

    session.commit()
    return app
