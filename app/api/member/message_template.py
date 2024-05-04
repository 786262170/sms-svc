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
from app.model.message import MessageTemplate, MessageTemplateStatus, MessageType
from app.model.user import User

router = APIRouter()


class MessageTemplateResponse(OrmBaseModel):
    id: str = Field(..., description='消息模板ID')
    created_timestamp: int = Field(..., description='创建时间')

    # user_id: str = Field(..., description='用户ID')

    name: str = Field(None, description='名字')

    content: str = Field(..., description='内容')
    type: MessageType = Field(..., description=MessageType.__doc__)

    # shared: int = Field(None, description='共享')
    # tags: int = Field(None, description='用户标签')
    #
    # interests: int = Field(None, description='兴趣定位人群')

    status: MessageTemplateStatus = Field(..., description=MessageTemplateStatus.__doc__)
    invalid: int = Field(..., description='无效')


class MessageTemplateList(PaginateBase):
    items: List[MessageTemplateResponse] = []


@router.get('/list', response_model=MessageTemplateList)
def message_template_list(page: int = 1,
                          per_page: int = 5,
                          name: str = None,
                          type: int = None,
                          # shared: int = None,
                          # tags: int = None,
                          # interests: int = None,
                          status: int = None,
                          invalid: int = None,
                          created_begin_timestamp: int = None,
                          created_end_timestamp: int = None,
                          session: Session = Depends(GetSession(member_login_required))):
    """消息模板列表"""
    current_user = session.info['current_user']
    q = session.query(MessageTemplate)
    q = q.filter(MessageTemplate.user_id == current_user.id)

    if name is not None:
        q = q.filter(MessageTemplate.name.contains(name))

    if type is not None:
        q = q.filter(MessageTemplate.type.op('&')(type))

    # if shared is not None:
    #     q = q.filter(MessageTemplate.shared == shared)
    #
    # if tags is not None:
    #     q = q.filter(MessageTemplate.tags.op('&')(tags))
    #
    # if interests is not None:
    #     q = q.filter(MessageTemplate.interests.op('&')(interests))

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
                             session: Session = Depends(GetSession(member_login_required))):
    """消息模板详情"""
    current_user = session.info['current_user']
    message_template = session.query(MessageTemplate).filter(MessageTemplate.user_id == current_user.id,
                                                             MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    return message_template


@router.delete('/details/{id}')
def message_template_details(id: str,
                             session: Session = Depends(GetSession(member_login_required))):
    """删除消息模板"""
    current_user = session.info['current_user']
    message_template = session.query(MessageTemplate).filter(MessageTemplate.user_id == current_user.id,
                                                             MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    # session.delete(message_template)
    message_template.invalid = 1
    session.commit()

    return {}


class MessageTemplateRequest(BaseModel):

    name: str = Field(..., description='名字')
    content: str = Field(..., description='内容')
    type: MessageType = Field(..., description=MessageType.__doc__)

    # shared: int = Field(None, description='共享(当前版本不传)')
    # tags: int = Field(None, description='用户标签(当前版本不传)')
    #
    # interests: int = Field(None, description='兴趣定位人群(当前版本不传)')
    #
    # status: MessageTemplateStatus = Field(None, description=MessageTemplateStatus.__doc__)


@router.post('/create', response_model=MessageTemplateResponse)
def create_message_template(data: MessageTemplateRequest,
                            session: Session = Depends(GetSession(member_login_required))):
    """添加消息模板"""
    current_user: User = session.info['current_user']
    if data.content is None:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_CONTENT_EMPTY, '消息模板内容为空')

    message_template = MessageTemplate(user_id=current_user.id,
                                       name=data.name,
                                       content=data.content,
                                       type=data.type.value,
                                       # shared=data.shared,
                                       # tags=data.tags,
                                       # interests=data.interests,
                                       status=MessageTemplateStatus.SUCCESS.value)
    session.add(message_template)
    session.commit()
    return message_template


class MessageTemplateModifyRequest(BaseModel):

    name: str = Field(None, description='名字')
    content: str = Field(None, description='内容')
    type: MessageType = Field(None, description=MessageType.__doc__)

    # shared: int = Field(None, description='共享(当前版本不传)')
    # tags: int = Field(None, description='用户标签(当前版本不传)')
    #
    # interests: int = Field(None, description='兴趣定位人群(当前版本不传)')
    #
    # status: MessageTemplateStatus = Field(None, description=MessageTemplateStatus.__doc__)


@router.put('/details/{id}', response_model=MessageTemplateResponse)
def modify_message_template(id: str,
                            data: MessageTemplateModifyRequest,
                            session: Session = Depends(GetSession(member_login_required))):
    """修改消息模板"""
    current_user = session.info['current_user']
    message_template = session.query(MessageTemplate).filter(MessageTemplate.user_id == current_user.id,
                                                             MessageTemplate.id == id).first()
    if not message_template:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_NOT_EXIST, '消息模板不存在')

    # if data.status is not None and data.status != MessageTemplateStatus.CANCEL:
    #     raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_STATUS_ERR, '消息模板状态错误')
    #
    # dt = dict()
    # if data.name is not None:
    #     dt.update(dict(name=data.name))
    #
    # if data.content is not None:
    #     dt.update(dict(content=data.content))
    #
    # if data.type is not None:
    #     dt.update(dict(type=data.type.value))
    #
    # if data.shared is not None:
    #     dt.update(dict(shared=data.shared))
    #
    # if data.tags is not None:
    #     dt.update(dict(tags=data.tags))
    #
    # if data.interests is not None:
    #     dt.update(dict(interests=data.interests))
    #
    # if data.status is not None:
    #     dt.update(dict(status=data.status.value))
    #
    # ret = session.query(MessageTemplate).filter(
    #     MessageTemplate.user_id == current_user.id, MessageTemplate.id == id,
    #     MessageTemplate.status == MessageTemplateStatus.PENDING.value).update(dt)
    # if ret != 1:
    #     raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_STATUS_ERR, '消息模板状态错误')

    if data.name is not None:
        message_template.name = data.name

    if data.content is not None:
        message_template.content = data.content

    if data.type is not None:
        message_template.type = data.type.value

    session.commit()
    return message_template
