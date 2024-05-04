# -*- coding: utf-8 -*-
import time
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.member import member_login_required
from app.model import timestamp_to_datetime
from app.model.application import Application
from app.model.user import User

router = APIRouter()


class ApplicationResponse(OrmBaseModel):
    created_timestamp: int
    app_id: str = Field(..., description='应用ID')
    # user_id: str = Field(..., description='用户ID')
    name: str = Field(..., description='应用名称')
    app_key: str = Field(..., description='应用 key')
    # secret_key: str = Field(..., description='密钥')
    # sms_hook_url: str = Field(None, description='sms失败回调的 url')
    # invalid: int = Field(..., description='无效')


class ApplicationList(PaginateBase):
    items: List[ApplicationResponse] = []


@router.get('/list', response_model=ApplicationList)
def application_list(page: int = 1,
                     per_page: int = 5,
                     # invalid: int = 0,
                     created_begin_timestamp: int = None,
                     created_end_timestamp: int = None,
                     session: Session = Depends(GetSession(member_login_required))):
    """应用列表"""
    current_user = session.info['current_user']
    q = session.query(Application)
    q = q.filter(Application.user_id == current_user.id)
    q = q.filter(Application.invalid == 0)

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
                        session: Session = Depends(GetSession(member_login_required))):
    """应用详情"""
    current_user = session.info['current_user']
    app = session.query(Application).filter(Application.user_id == current_user.id,
                                            Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    return app


@router.delete('/details/{app_id}')
def application_details(app_id: str,
                        session: Session = Depends(GetSession(member_login_required))):
    """删除应用"""
    current_user = session.info['current_user']
    app = session.query(Application).filter(Application.user_id == current_user.id,
                                            Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    # session.delete(app)
    app.invalid = 1
    session.commit()

    return {}


class ApplicationRequest(BaseModel):
    name: str = Field(None, description='应用名称')
    # sms_hook_url: str = Field(None, description='应用名称')


@router.post('/create', response_model=ApplicationResponse)
def create_application(data: ApplicationRequest,
                       session: Session = Depends(GetSession(member_login_required))):
    """添加应用"""
    current_user: User = session.info['current_user']

    if data.name is None:
        raise BsException(BsExceptionEnum.APP_NAME_NOT_EXIST, '应用名称不存在')

    app = Application.create(session,
                             user_id=current_user.id,
                             name=data.name)

    session.commit()
    return app


class ApplicationModifyRequest(BaseModel):
    name: str = Field(None, description='应用名称')
    refresh_app_key: bool = Field(None, description='更新app_key')
    # sms_hook_url: str = Field(None, description='应用名称')


@router.put('/details/{app_id}', response_model=ApplicationResponse)
def modify_application(app_id: str,
                       data: ApplicationModifyRequest,
                       session: Session = Depends(GetSession(member_login_required))):
    """修改应用"""
    current_user = session.info['current_user']
    app: Application = session.query(Application).filter(Application.user_id == current_user.id,
                                                         Application.app_id == app_id).first()
    if not app:
        raise BsException(BsExceptionEnum.APP_NOT_EXIST, '应用不存在')

    if data.name is not None:
        app.name = data.name
    if data.refresh_app_key:
        app._app_key = Application.generate_app_key()
    # if data.sms_hook_url is not None:
    #     app.sms_hook_url = data.sms_hook_url

    session.commit()
    return app
