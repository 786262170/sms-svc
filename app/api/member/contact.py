# -*- coding: utf-8 -*-
import json
import time
import pandas as pd
from io import BytesIO
from typing import List

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, Form
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.api import PaginateBase, OrmBaseModel, GetSession, BsException, BsExceptionEnum
from app.api.member import member_login_required
from app.model import timestamp_to_datetime
from app.model.contact import Contact, ContactGender, ContactState, ContactGroup
from app.model.user import User

router = APIRouter()


class ContactGroupResponse(OrmBaseModel):
    id: int = Field(..., description='分组ID')
    name: str = Field(None, description='分组名称')


class ContactGroupRequest(BaseModel):
    name: str = Field(None, description='分组名称')


@router.post('/add_group', response_model=ContactGroupResponse)
def add_group(data: ContactGroupRequest,
              session: Session = Depends(GetSession(member_login_required))):
    """添加分组"""
    current_user = session.info['current_user']
    group = session.query(ContactGroup).filter(ContactGroup.name == data.name).first()

    if group:
        raise BsException(BsExceptionEnum.GROUP_EXIST, '分组已经存在')

    group = ContactGroup(user_id=current_user.id, name=data.name)
    session.add(group)
    session.commit()
    return group


@router.put('/group/details/{id}', response_model=ContactGroupResponse)
def modify_contact(id: str,
                   data: ContactGroupRequest,
                   session: Session = Depends(GetSession(member_login_required))):
    """修改分组名称"""
    current_user = session.info['current_user']
    group = session.query(ContactGroup).filter(ContactGroup.user_id == current_user.id,
                                               ContactGroup.id == id).first()
    if not group:
        raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '组不存在')

    if data.name is not None:
        group.name = data.name

    session.commit()
    return group


class GroupList(PaginateBase):
    items: List[ContactGroupResponse] = []


@router.get('/group_list', response_model=GroupList)
def group_list(page: int = 1,
               per_page: int = 5,
               name: str = None,
               created_begin_timestamp: int = None,
               created_end_timestamp: int = None,
               session: Session = Depends(GetSession(member_login_required))):
    """分组列表"""
    current_user = session.info['current_user']
    q = session.query(ContactGroup)
    q = q.filter(ContactGroup.user_id == current_user.id)
    if name:
        q = q.filter(ContactGroup.name.contains(name))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(ContactGroup.created_at >= timestamp_to_datetime(begin_timestamp),
                             ContactGroup.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(ContactGroup.created_at.desc())
    return q.paginate(page, per_page)


class ContactResponse(OrmBaseModel):
    id: str = Field(..., description='联系人ID')
    created_timestamp: int = Field(..., description='创建时间')

    user_id: str = Field(..., description='用户ID')

    # group_id: int = Field(None, description='组号ID')

    first_name: str = Field(None, description='首名字')
    last_name: str = Field(None, description='名字')

    country: str = Field(None, description='国家')
    mobile: str = Field(None, description='手机号码')
    email: str = Field(None, description='邮箱')

    title: str = Field(None, description='标题')
    company: str = Field(None, description='公司')

    custom: dict = Field(None, description='自定义字段')
    blacklisted: str = Field(None, description='是否黑名单')

    group: ContactGroupResponse = Field(None, description='分组')


class ContactList(PaginateBase):
    items: List[ContactResponse] = []


@router.get('/list', response_model=ContactList)
def contact_list(page: int = 1,
                 per_page: int = 5,
                 group_id: int = None,
                 country: str = None,
                 mobile: str = None,
                 first_name: str = None,
                 last_name: str = None,
                 created_begin_timestamp: int = None,
                 created_end_timestamp: int = None,
                 session: Session = Depends(GetSession(member_login_required))):
    """联系人列表"""
    current_user = session.info['current_user']
    q = session.query(Contact)
    q = q.filter(Contact.user_id == current_user.id)
    if group_id:
        q = q.filter(Contact.group_id == group_id)
    if country:
        q = q.filter(Contact.country == country)
    if mobile:
        q = q.filter(Contact.mobile == mobile)
    if first_name:
        q = q.filter(Contact.first_name == first_name)
    if last_name:
        q = q.filter(Contact.last_name == last_name)

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
                    session: Session = Depends(GetSession(member_login_required))):
    """联系人详情"""
    current_user = session.info['current_user']
    contact = session.query(Contact).filter(Contact.user_id == current_user.id,
                                            Contact.id == id).first()
    if not contact:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '联系人不存在')

    return contact


class DeleteRequest(BaseModel):
    ids: List[str] = Field(None, description='删除id 列表')


@router.post('/delete')
def contact_details(data: DeleteRequest,
                    session: Session = Depends(GetSession(member_login_required))):
    """删除联系人"""
    current_user = session.info['current_user']
    session.query(Contact).filter(Contact.user_id == current_user.id,
                                  Contact.id.in_(data.ids)).delete(synchronize_session=False)
    # contact.invalid = 1
    session.commit()

    return {}


class ContactRequest(BaseModel):
    group_id: int = Field(None, description='组号')

    first_name: str = Field(None, description='首名字')
    last_name: str = Field(None, description='名字')
    # gender: ContactGender = Field(None, description=ContactGender.__doc__)

    country: str = Field(None, description='国家')
    mobile: str = Field(None, description='手机号码')
    email: str = Field(None, description='邮箱')

    title: str = Field(None, description='标题')
    company: str = Field(None, description='公司')

    custom: dict = Field(None, description='自定义字段')
    blacklisted: str = Field(None, description='是否黑名单')


@router.post('/create', response_model=ContactResponse)
def create_contact(data: ContactRequest,
                   session: Session = Depends(GetSession(member_login_required))):
    """添加联系人"""
    current_user: User = session.info['current_user']

    if data.group_id is not None:
        group = session.query(ContactGroup).filter(ContactGroup.user_id == current_user.id,
                                                   ContactGroup.id == data.group_id).first()
        if not group:
            raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '组不存在')

    # gender = None
    # if data.gender is not None:
    #     gender = data.gender.value

    # state = None
    # if data.state is not None:
    #     state = data.state.value

    contact = Contact(user_id=current_user.id,
                      group_id=data.group_id,
                      first_name=data.first_name,
                      last_name=data.last_name,
                      # gender=gender,
                      country=data.country,
                      mobile=data.mobile,
                      email=data.email,
                      # state=state,
                      title=data.title,
                      blacklisted=data.blacklisted,
                      company=data.company,
                      custom_json=json.dumps(data.custom))
    session.add(contact)
    session.commit()
    return contact


@router.post('/upload')
def upload_contact(xlsx_file: bytes = File(..., description='上传xlsx文件'),
                   group_id: int = Form(..., description='起指定分组'),
                   session: Session = Depends(GetSession(member_login_required))):
    """上传联系人"""
    current_user: User = session.info['current_user']

    group = session.query(ContactGroup).filter(ContactGroup.user_id == current_user.id,
                                               ContactGroup.id == group_id).first()
    if not group:
        raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '组不存在')

    df = pd.read_excel(xlsx_file)
    df = df.fillna('')
    columns_name = ['Country', 'First Name', 'Last Name', 'Phone', 'Email', 'Title', 'Company', 'Blacklisted']
    if df.columns.tolist()[:8] != columns_name:
        raise BsException(BsExceptionEnum.XLSX_COLUMNS_ERROR, '文件列错误')
    for i in range(df.shape[0]):
        data_dict = df.iloc[i, 0:8].to_dict()
        custom_dict = df.iloc[i, 8:].to_dict()
        contact = Contact(user_id=current_user.id,
                          group_id=group_id,
                          first_name=data_dict['First Name'],
                          last_name=data_dict['Last Name'],
                          # gender=data_dict['Last Name'],
                          country=data_dict['Country'],
                          mobile=data_dict['Phone'],
                          email=data_dict['Email'],
                          title=data_dict['Title'],
                          company=data_dict['Company'],
                          blacklisted=data_dict['Blacklisted'],
                          custom_json=json.dumps(custom_dict))
        session.add(contact)
    session.commit()
    return {}


@router.put('/details/{id}', response_model=ContactResponse)
def modify_contact(id: str,
                   data: ContactRequest,
                   session: Session = Depends(GetSession(member_login_required))):
    """修改联系人"""
    current_user = session.info['current_user']
    contact = session.query(Contact).filter(Contact.user_id == current_user.id,
                                            Contact.id == id).first()
    if not contact:
        raise BsException(BsExceptionEnum.CONTACT_NOT_EXIST, '联系人不存在')

    if data.group_id is not None:
        group = session.query(ContactGroup).filter(ContactGroup.user_id == current_user.id,
                                                   ContactGroup.id == data.group_id).first()
        if not group:
            raise BsException(BsExceptionEnum.GROUP_NOT_EXIST, '组不存在')

        contact.group_id = data.group_id

    if data.first_name is not None:
        contact.first_name = data.first_name

    if data.last_name is not None:
        contact.last_name = data.last_name

    # if data.gender is not None:
    #     contact.gender = data.gender.value

    if data.country is not None:
        contact.country = data.country

    if data.mobile is not None:
        contact.mobile = data.mobile

    if data.email is not None:
        contact.email = data.email

    if data.title is not None:
        contact.title = data.title

    if data.company is not None:
        contact.company = data.company

    if data.blacklisted is not None:
        contact.blacklisted = data.blacklisted

    if data.custom is not None:
        contact.custom_json = json.dumps(data.custom)

    session.commit()
    return contact


@router.get("/contact/demo", response_description='xlsx')
async def download_demo():
    """下载联系人模板"""
    f = open("doc/demo.xlsx", "br")

    headers = {
        'Content-Disposition': 'attachment; filename="demo.xlsx"'
    }
    return StreamingResponse(f, headers=headers)
