# -*- coding: utf-8 -*-
import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship

from app.model import UuidBase, BaseModel, AutoIncrementBase


class SmsProductType(int, Enum):
    """短信类型 1：验证码; 2：营销;"""
    VERIFY = 1  # 验证码
    MESSAGING = 2  # 营销


class SmsProductProvider(int, Enum):
    """供应商 0：牛信; 1：天一泓; 2: cm.com"""
    NX = 0  # 0 牛信
    SKYLINE = 1  # 天一泓
    CMCOM = 2  # cm.com


class SmsProduct(UuidBase):
    __tablename__ = 'sms_product'

    channel_name = sa.Column(sa.String(36), sa.ForeignKey('sms_channel.name'), nullable=False)

    admin_user_id = sa.Column(sa.String(36), sa.ForeignKey('admin_user.id'), nullable=False)

    # 手机国家码 存在重复，所以需要国家
    country = sa.Column(sa.String(36), nullable=False, comment='国家')
    country_code = sa.Column(sa.Integer, nullable=False, comment='手机国家码')  # 国家代码

    type = sa.Column(sa.Integer, default=SmsProductType.VERIFY.value, nullable=False)  # 支持的类型

    provider = sa.Column(sa.Integer, default=SmsProductProvider.NX.value, nullable=False)  # 供应商

    channel_price = sa.Column(sa.Numeric(24, 8), default=0, nullable=False, comment='通道价格')  # 成本价价格
    price = sa.Column(sa.Numeric(24, 8), default=0, nullable=False, comment='默认价格')  # 价格
    cost_price = sa.Column(sa.Numeric(24, 8), default=0, nullable=False, comment='成本价格')  # 成本价价格
    list_price = sa.Column(sa.Numeric(24, 8), default=0, nullable=False, comment='通道最高价格')  # 通道最高价格

    invalid = sa.Column(sa.Integer, default=0, nullable=False)  # 0为有效 1为无效

    admin_user = relationship('AdminUser', foreign_keys=[admin_user_id])

    channel = relationship('SmsChannel', foreign_keys=[channel_name])

    __table_args__ = (
        sa.UniqueConstraint('admin_user_id', 'country', 'channel_name'),)

    @staticmethod
    def initialize(session):
        pass


class SmsChannel(BaseModel):
    __tablename__ = 'sms_channel'

    name = sa.Column(sa.String(36), primary_key=True)
    type = sa.Column(sa.Integer, default=SmsProductType.VERIFY.value, nullable=False)  # 支持的类型
    provider = sa.Column(sa.Integer, default=SmsProductProvider.NX.value, nullable=False)  # 供应商
    app_id = sa.Column(sa.String(36), nullable=False)
    app_key = sa.Column(sa.String(128), nullable=False)

    @property
    def get_sdk(self):
        from sdk.nxcloud import NXCloudSms
        from sdk.skyline import SkyLineSms
        from sdk.cmcom import CmcomSms
        if self.provider == SmsProductProvider.NX.value:
            return NXCloudSms(self.app_id, self.app_key)
        elif self.provider == SmsProductProvider.CMCOM.value:
            return CmcomSms(self.app_id, self.app_key)
        else:
            return SkyLineSms(self.app_id, self.app_key)

    def send_sms(self, phone: list, content):
        self.get_sdk.send_sms(phone, content)

    @staticmethod
    def initialize(session):
        nx_whosale = session.query(SmsChannel).filter(SmsChannel.name == 'nx_whosale').first()

        if nx_whosale is None:
            # 生成虚拟用户
            nx_whosale = SmsChannel(name='nx_whosale',
                                    type=SmsProductType.MESSAGING.value,
                                    provider=SmsProductProvider.NX.value,
                                    app_id='YYOVKrDt',
                                    app_key='oGdoUUOR')
            session.add(nx_whosale)
            session.commit()
        nx_regular = session.query(SmsChannel).filter(SmsChannel.name == 'nx_regular').first()
        if nx_regular is None:
            nx_regular = SmsChannel(name='nx_regular',
                                    type=SmsProductType.VERIFY.value,
                                    provider=SmsProductProvider.NX.value,
                                    app_id='Pb44dHph',
                                    app_key='rXtQw3Dt')
            session.add(nx_regular)
            session.commit()
        nx_premium = session.query(SmsChannel).filter(SmsChannel.name == 'nx_premium').first()
        if nx_premium is None:
            nx_premium = SmsChannel(name='nx_premium',
                                    type=SmsProductType.VERIFY.value,
                                    provider=SmsProductProvider.NX.value,
                                    app_id='iVnTBXir',
                                    app_key='D3UyOpwO')
            session.add(nx_premium)
            session.commit()

        skyline_01 = session.query(SmsChannel).filter(SmsChannel.name == 'skyline_01').first()
        if skyline_01 is None:
            skyline_01 = SmsChannel(name='skyline_01',
                                    type=SmsProductType.VERIFY.value,
                                    provider=SmsProductProvider.SKYLINE.value,
                                    app_id='cs_ezimvo',
                                    app_key='0IOoX7qH')
            session.add(skyline_01)
            session.commit()

        skyline_02 = session.query(SmsChannel).filter(SmsChannel.name == 'skyline_02').first()
        if skyline_02 is None:
            skyline_02 = SmsChannel(name='skyline_02',
                                    type=SmsProductType.MESSAGING.value,
                                    provider=SmsProductProvider.SKYLINE.value,
                                    app_id='cs_af9hmu',
                                    app_key='BFnXraHl')
            session.add(skyline_02)
            session.commit()

        skyline_03 = session.query(SmsChannel).filter(SmsChannel.name == 'skyline_03').first()
        if skyline_03 is None:
            skyline_03 = SmsChannel(name='skyline_03',
                                    type=SmsProductType.MESSAGING.value,
                                    provider=SmsProductProvider.SKYLINE.value,
                                    app_id='vze4G0B3',
                                    app_key='3UfoGWt9')
            session.add(skyline_03)
            session.commit()

        cm_verify = session.query(SmsChannel).filter(SmsChannel.name == 'cm_verify').first()
        if cm_verify is None:
            cm_verify = SmsChannel(name='cm_verify',
                                    type=SmsProductType.VERIFY.value,
                                    provider=SmsProductProvider.CMCOM.value,
                                    app_id='dizpay',
                                    app_key='07da6932-ee90-475a-8802-f42d2dfef2c8')
            session.add(cm_verify)
            session.commit()

        cm_domestic = session.query(SmsChannel).filter(SmsChannel.name == 'cm_domestic').first()
        if cm_domestic is None:
            cm_domestic = SmsChannel(name='cm_domestic',
                                    type=SmsProductType.MESSAGING.value,
                                    provider=SmsProductProvider.CMCOM.value,
                                    app_id='dizpay',
                                    app_key='e366267b-e824-43a0-923c-2319c49196ad')
            session.add(cm_domestic)
            session.commit()

        cm_intl = session.query(SmsChannel).filter(SmsChannel.name == 'cm_intl').first()
        if cm_intl is None:
            cm_intl = SmsChannel(name='cm_intl',
                                    type=SmsProductType.MESSAGING.value,
                                    provider=SmsProductProvider.CMCOM.value,
                                    app_id='dizpay',
                                    app_key='dad5b394-5dfb-4e60-ab5b-e3dcf3bd093a')
            session.add(cm_intl)
            session.commit()


class SmsSpecialCheck(AutoIncrementBase):
    __tablename__ = 'sms_special_check'

    channel_name = sa.Column(sa.String(36), sa.ForeignKey('sms_channel.name'), nullable=False)

    page_size = sa.Column(sa.SmallInteger, default=500, nullable=False)  # 页大小
    num = sa.Column(sa.Integer, default=0, nullable=False)  # 当前已校验的数目

    date = sa.Column(DateTime, nullable=False)

    @staticmethod
    def initialize(session):
        channel_list = session.query(SmsChannel).filter(SmsChannel.provider == SmsProductProvider.NX.value).all()

        for channel in channel_list:
            check = session.query(SmsSpecialCheck).filter(SmsSpecialCheck.channel_name == channel.name).first()
            if check is None:
                # 生成虚拟用户
                now = datetime.datetime.now()
                check = SmsSpecialCheck(channel_name=channel.name, date=datetime.datetime(now.year, now.month, now.day))
                session.add(check)
                session.commit()


class SmsSpecialNotFoundRecord(AutoIncrementBase):
    __tablename__ = 'sms_special_not_found_record'

    channel_name = sa.Column(sa.String(36), sa.ForeignKey('sms_channel.name'), nullable=False)

    num = sa.Column(sa.Integer, default=0, nullable=False)  # 当前已校验的数目

    date = sa.Column(DateTime, nullable=False)

    info = sa.Column(sa.Text, nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('channel_name', 'num', 'date'),)
