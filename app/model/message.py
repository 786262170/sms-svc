# -*- coding: utf-8 -*-
import sqlalchemy as sa

from enum import Enum

from sqlalchemy.sql.expression import false

from sdk import SmsStatus
from sqlalchemy.orm import relationship
from app.model import UuidBase, AutoIncrementBase, datetime_to_timestamp


class MessageType(int, Enum):
    """类型 1：普通; 2：营销;"""
    NORMAL = 1  # 普通
    MESSAGING = 2  # 营销


class MessageStatus(int, Enum):
    """短信的处理状态 0:未处理；1:已处理；"""
    PENDING = 0
    FINISH = 1


class MessageTemplateStatus(int, Enum):
    """模板状态(此版本不填) 1:待审核；2:成功；4:失败；8:驳回；16:取消"""
    PENDING = 1
    SUCCESS = 2
    FAIL = 4
    REJECT = 8
    CANCEL = 16


class MessageTemplate(UuidBase):
    __tablename__ = 'message_template'

    user_id = sa.Column(sa.String(36), sa.ForeignKey(
        'user.id'), nullable=False)

    name = sa.Column(sa.String(60))
    content = sa.Column(sa.Text, nullable=False)

    type = sa.Column(
        sa.Integer, default=MessageType.NORMAL.value, nullable=False)  # 支持的类型

    shared = sa.Column(sa.SmallInteger, default=0)  # 0私有 1共享
    tags = sa.Column(sa.Integer, default=0)  # 用户标签 1, 2, 4, 8, 16 (行业类型)

    interests = sa.Column(sa.Integer, default=0)  # 兴趣定位人群

    status = sa.Column(
        sa.Integer, default=MessageTemplateStatus.PENDING.value, nullable=False)  # 审核状态
    invalid = sa.Column(sa.Integer, default=0, nullable=False)  # 0为有效 1为无效

    user = relationship('User', foreign_keys=[user_id])


class Message(UuidBase):
    __tablename__ = 'message'

    user_id = sa.Column(sa.String(36), sa.ForeignKey(
        'user.id'), nullable=False)
    app_id = sa.Column(sa.String(18), sa.ForeignKey(
        'application.app_id'), nullable=False)
    group_id = sa.Column(sa.Integer, sa.ForeignKey('contact_group.id'))

    mobile = sa.Column(sa.Text(10000000), nullable=False)
    filtered_mobile = sa.Column(sa.Text(10000000), nullable=True)

    type = sa.Column(
        sa.SmallInteger, default=MessageType.NORMAL.value, nullable=False)  # 支持的类型
    content = sa.Column(sa.Text, nullable=False)

    status = sa.Column(
        sa.SmallInteger, default=MessageStatus.PENDING.value)  # 0 未处理  1 已处理
    processed_at = sa.Column(sa.DateTime)

    user = relationship('User', foreign_keys=[user_id])
    application = relationship('Application', foreign_keys=[app_id])
    group = relationship('ContactGroup', foreign_keys=[group_id])


class MessageTimingFrequency(int, Enum):
    """定时短信的频率 1:一次；2:每天；"""
    ONCE = 1
    EVERY_DAY = 2


class MessageTiming(UuidBase):
    __tablename__ = 'message_timing'

    user_id = sa.Column(sa.String(36), sa.ForeignKey(
        'user.id'), nullable=False)
    app_id = sa.Column(sa.String(18), sa.ForeignKey(
        'application.app_id'), nullable=False)
    group_id = sa.Column(sa.Integer, sa.ForeignKey('contact_group.id'))

    mobile = sa.Column(sa.Text, nullable=False)
    mobile_count = sa.Column(sa.Integer, nullable=False)
    filtered_mobile = sa.Column(sa.Text, nullable=True)
    filtered_mobile_count = sa.Column(sa.Integer, nullable=True)
    delivered_count = sa.Column(sa.Integer, default=0, nullable=False)
    type = sa.Column(
        sa.SmallInteger, default=MessageType.NORMAL.value, nullable=False)  # 支持的类型
    content = sa.Column(sa.Text, nullable=False)

    timing_at = sa.Column(sa.DateTime, nullable=False)
    frequency = sa.Column(
        sa.SmallInteger, default=MessageTimingFrequency.ONCE.value, nullable=False)

    status = sa.Column(
        sa.SmallInteger, default=MessageStatus.PENDING.value)  # 0 未处理  1 已处理
    processed_at = sa.Column(sa.DateTime)

    invalid = sa.Column(sa.SmallInteger, default=0,
                        nullable=False)  # 0为有效 1为无效

    user = relationship('User', foreign_keys=[user_id])
    application = relationship('Application', foreign_keys=[app_id])
    group = relationship('ContactGroup', foreign_keys=[group_id])

    @property
    def timing_timestamp(self):
        return datetime_to_timestamp(self.timing_at)


class MessageCheck(AutoIncrementBase):
    __tablename__ = 'message_check'

    user_id = sa.Column(sa.String(36), sa.ForeignKey(
        'user.id'), nullable=False)  # 为了方便查询短信列表添加该字段
    message_id = sa.Column(sa.String(36), sa.ForeignKey('message.id'))
    message_timing_id = sa.Column(
        sa.String(36), sa.ForeignKey('message_timing.id'))
    sms_product_id = sa.Column(sa.String(36), sa.ForeignKey(
        'sms_product.id'), nullable=False)

    # 0 未处理  1 已处理 2 需特殊处理
    status = sa.Column(sa.SmallInteger, default=MessageStatus.PENDING.value)
    processed_at = sa.Column(sa.DateTime)

    country = sa.Column(sa.String(36), nullable=False, comment='国家')
    phone_number = sa.Column(sa.String(36), nullable=False)  # 手机号

    content = sa.Column(sa.Text, nullable=False)  # 实际发送的内容

    message_number = sa.Column(sa.String(36), comment='sms发送后返回的number')
    message_status = sa.Column(
        sa.Integer, default=SmsStatus.PENDING.value, nullable=False)  # 状态码, 参见 SMSStatus

    price = sa.Column(sa.Numeric(24, 8), default=0, nullable=False)  # 价格

    message = relationship('Message', foreign_keys=[message_id])
    message_timing = relationship(
        'MessageTiming', foreign_keys=[message_timing_id])
    sms_product = relationship('SmsProduct', foreign_keys=[sms_product_id])

    @property
    def mobile(self):
        return self.phone_number
