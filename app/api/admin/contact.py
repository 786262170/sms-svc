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
from app.model.contact import Contact, ContactGender, ContactState
from app.model.admin_user import AdminUserRole
from app.model.user import User

router = APIRouter()


class ContactResponse(OrmBaseModel):
    id: str = Field(..., description='联系人ID')
    created_timestamp: int = Field(..., description='创建时间')

    user_id: str = Field(..., description='用户ID')

    group: int = Field(..., description='组号')

    first_name: str = Field(None, description='首名字')
    last_name: str = Field(None, description='名字')
    gender: ContactGender = Field(..., description=ContactGender.__doc__)

    country_code: str = Field(None, description='区号')
    mobile: str = Field(None, description='手机号码')

    state: ContactState = Field(..., description=ContactState.__doc__)
    link: str = Field(None, description='链接')
    tags: int = Field(..., description='用户标签')

    interests: int = Field(None, description='兴趣定位人群')
    extra: str = Field(None, description='额外信息')


class ContactList(PaginateBase):
    items: List[ContactResponse] = []


@router.get('/list', response_model=ContactList)
def contact_list(page: int = 1,
                 per_page: int = 5,
                 user_id: str = None,
                 group: int = 0,
                 invalid: int = 0,
                 state: int = None,
                 tags: int = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """联系人列表"""
    q = session.query(Contact)
    if user_id is not None:
        q = q.filter(Contact.user_id == user_id)
    q = q.filter(Contact.group == group)
    q = q.filter(Contact.invalid == invalid)
    if state is not None:
        q = q.filter(Contact.state == state)
    if tags is not None:
        q = q.filter(Contact.tags.op('&')(tags))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(Contact.created_at >= timestamp_to_datetime(begin_timestamp),
                             Contact.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(Contact.created_at.desc())
    return q.paginate(page, per_page)


@router.get('/details/{id}', response_model=ContactResponse)
def contact_details(id: str,
                    session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """联系人详情"""
    contact = session.query(Contact).filter(Contact.id == id).first()
    if not contact:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '联系人不存在')

    return contact


@router.delete('/details/{id}')
def contact_details(id: str,
                    session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """删除联系人"""
    contact = session.query(Contact).filter(Contact.id == id).first()
    if not contact:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '联系人不存在')

    # session.delete(contact)
    contact.invalid = 1
    session.commit()

    return {}


class ContactRequest(BaseModel):
    user_id: str = Field(None, description='用户ID')

    group: int = Field(None, description='组号')

    first_name: str = Field(None, description='首名字')
    last_name: str = Field(None, description='名字')
    gender: ContactGender = Field(None, description=ContactGender.__doc__)

    country_code: str = Field(None, description='国际电话区号')
    mobile: str = Field(None, description='手机号')

    state: ContactState = Field(None, description=ContactState.__doc__)
    link: str = Field(None, description='链接')
    tags: int = Field(None, description='用户标签')

    interests: int = Field(None, description='兴趣定位人群')
    extra: str = Field(None, description='额外信息')


@router.post('/create', response_model=ContactResponse)
def create_contact(data: ContactRequest,
                   session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """添加联系人"""
    if data.user_id is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户ID不存在')

    user = session.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, '用户不存在')

    gender = None
    if data.gender is not None:
        gender = data.gender.value

    state = None
    if data.state is not None:
        state = data.state.value

    contact = Contact(user_id=data.user_id,
                      first_name=data.first_name,
                      last_name=data.last_name,
                      gender=gender,
                      country_code=data.country_code,
                      mobile=data.mobile,
                      state=state,
                      link=data.link,
                      tags=data.tags,
                      interests=data.interests,
                      extra=data.extra)
    session.add(contact)
    session.commit()
    return contact


@router.put('/details/{id}', response_model=ContactResponse)
def modify_contact(id: str,
                   data: ContactRequest,
                   session: Session = Depends(GetSession(admin_login_required, AdminUserRole.SUPER))):
    """修改联系人"""
    contact = session.query(Contact).filter(Contact.id == id).first()
    if not contact:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '联系人不存在')

    if data.group is not None:
        contact.group = data.group

    if data.first_name is not None:
        contact.first_name = data.first_name

    if data.last_name is not None:
        contact.last_name = data.last_name

    if data.gender is not None:
        contact.gender = data.gender.value

    if data.country_code is not None:
        contact.country_code = data.country_code

    if data.mobile is not None:
        contact.mobile = data.mobile

    if data.state is not None:
        contact.state = data.state.value

    if data.link is not None:
        contact.link = data.link

    if data.tags is not None:
        contact.tags = data.tags

    if data.interests is not None:
        contact.interests = data.interests

    if data.extra is not None:
        contact.extra = data.extra

    session.commit()
    return contact

