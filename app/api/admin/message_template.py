# -*- coding: utf-8 -*-
import time
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.admin import admin_login_required
from app.model import timestamp_to_datetime
from app.model.message import MessageTemplate, MessageTemplateStatus
from app.model.admin_user import AdminUserRole
from app.model.user import User

router = APIRouter()


class MessageTemplateResponse(OrmBaseModel):
    id: str = Field(..., description='消息模板ID')
    created_timestamp: int = Field(..., description='创建时间')

    user_id: str = Field(..., description='用户ID')

    name: str = Field(None, description='名字')

    content: str = Field(..., description='内容')
    shared: int = Field(None, description='共享')
    tags: int = Field(None, description='用户标签')

    interests: int = Field(None, description='兴趣定位人群')

    status: MessageTemplateStatus = Field(..., description=MessageTemplateStatus.__doc__)
    invalid: int = Field(..., description='无效')


class MessageTemplateList(PaginateBase):
    items: List[MessageTemplateResponse] = []


@router.get('/list', response_model=MessageTemplateList)
def message_template_list(page: int = 1,
                          per_page: int = 5,
                          user_id: str = None,
                          name: str = None,
                          shared: int = None,
                          tags: int = None,
                          interests: int = None,
                          status: int = None,
                          invalid: int = None,
                          created_begin_timestamp: int = None,
                          created_end_timestamp: int = None,
                          session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """消息模板列表"""
    q = session.query(MessageTemplate)
    if user_id is not None:
        q = q.filter(MessageTemplate.user_id == user_id)

    if name is not None:
        q = q.filter(MessageTemplate.name == name)

    if shared is not None:
        q = q.filter(MessageTemplate.shared == shared)

    if tags is not None:
        q = q.filter(MessageTemplate.tags.op('&')(tags))

    if interests is not None:
        q = q.filter(MessageTemplate.interests.op('&')(interests))

    if status is not None:
        q = q.filter(MessageTemplate.status.op('&')(status))

    if invalid is not None:
        q = q.filter(MessageTemplate.invalid == invalid)

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(MessageTemplate.created_at >= timestamp_to_datetime(begin_timestamp),
                             MessageTemplate.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(MessageTemplate.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/details/{id}', response_model=MessageTemplateResponse)
def message_template_details(id: str,
                             session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """消息模板详情"""
    message_template = session.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    return message_template


@router.delete('/details/{id}')
def message_template_details(id: str,
                             session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """删除消息模板"""
    message_template = session.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    # session.delete(message_template)
    message_template.invalid = 1
    session.commit()

    return {}


class MessageTemplateRequest(BaseModel):
    user_id: str = Field(None, description='用户ID')

    name: str = Field(None, description='名字')
    content: str = Field(None, description='内容')

    shared: int = Field(None, description='共享')
    tags: int = Field(None, description='用户标签')

    interests: int = Field(None, description='兴趣定位人群')

    status: MessageTemplateStatus = Field(None, description=MessageTemplateStatus.__doc__)


@router.post('/create', response_model=MessageTemplateResponse)
def create_message_template(data: MessageTemplateRequest,
                            session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """添加消息模板"""
    if data.user_id is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户ID不存在')

    user = session.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

    if data.content is None:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_CONTENT_EMPTY, '消息模板内容为空')

    message_template = MessageTemplate(user_id=data.user_id,
                                       name=data.name,
                                       content=data.content,
                                       shared=data.shared,
                                       tags=data.tags,
                                       interests=data.interests)
    session.add(message_template)
    session.commit()
    return message_template


@router.put('/details/{id}', response_model=MessageTemplateResponse)
def modify_message_template(id: str,
                            data: MessageTemplateRequest,
                            session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """修改消息模板"""
    message_template = session.query(MessageTemplate).filter(MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    dt = dict()
    if data.name is not None:
        dt.update(dict(name=data.name))

    if data.content is not None:
        dt.update(dict(content=data.content))

    if data.shared is not None:
        dt.update(dict(shared=data.shared))

    if data.tags is not None:
        dt.update(dict(tags=data.tags))

    if data.interests is not None:
        dt.update(dict(interests=data.interests))

    if data.status is not None:
        dt.update(dict(status=data.status.value))

    ret = session.query(MessageTemplate).filter(
        MessageTemplate.id == id,
        MessageTemplate.status == MessageTemplateStatus.PENDING.value).update(dt)
    if ret != 1:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_STATUS_ERR, '消息模板状态错误')

    session.commit()
    return message_template
