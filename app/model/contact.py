# -*- coding: utf-8 -*-
import json
import sqlalchemy as sa

from sqlalchemy.orm import relationship, Session
from enum import Enum

from app.model import app_config, UuidBase, AutoIncrementBase


class ContactGender(int, Enum):
    """联系人性别 0:未填; 1:男; 2:女;"""
    NOT_CHOICE = 0  # 0 未填
    BOY = 1  # 男
    GIRL = 2  # 女


class ContactState(int, Enum):
    """联系人状态 0:正常; 1:投递失败; 2:退订; 3:黑名单;"""
    OK = 0  # 0 正常
    FAIL = 1  # 投递失败
    UNSUBSCRIBE = 2  # 退订
    BLACKLIST = 3  # 黑名单


class ContactGroup(AutoIncrementBase):
    __tablename__ = 'contact_group'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)
    name = sa.Column(sa.String(60))

    __table_args__ = (sa.UniqueConstraint('user_id', 'name'),)

    @staticmethod
    def add_default(session: Session, user_id):
        group = ContactGroup(user_id=user_id, name='default')
        session.add(group)


class Contact(UuidBase):
    __tablename__ = 'contact'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)

    group_id = sa.Column(sa.Integer, sa.ForeignKey('contact_group.id'), nullable=False)

    first_name = sa.Column(sa.String(60))
    last_name = sa.Column(sa.String(60))

    gender = sa.Column(sa.Integer, default=0)

    country = sa.Column(sa.String(60))

    mobile = sa.Column(sa.String(16), nullable=False)  # 手机号
    email = sa.Column(sa.String(64))

    title = sa.Column(sa.String(128))
    company = sa.Column(sa.String(128))

    custom_json = sa.Column(sa.Text, default='{}')

    blacklisted = sa.Column(sa.String(16))

    user = relationship('User', foreign_keys=[user_id])
    group = relationship('ContactGroup', foreign_keys=[group_id])

    @property
    def custom(self):
        return json.loads(self.custom_json)
