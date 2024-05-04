# -*- coding: utf-8 -*-
from enum import Enum
from decimal import Decimal
import phonenumbers
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.model import AutoIncrementBase
from app.model.sms_product import SmsProductProvider, SmsProductType, SmsProduct, SmsChannel
from app.model.user import User


class SmsUser(AutoIncrementBase):
    __tablename__ = 'sms_user'

    user_id = sa.Column(sa.String(36), sa.ForeignKey(
        'user.id'), nullable=False)

    channel_name = sa.Column(sa.String(36), sa.ForeignKey(
        'sms_channel.name'), nullable=False)

    country = sa.Column(sa.String(36), nullable=False, comment='国家')
    country_code = sa.Column(
        sa.Integer, nullable=False, comment='手机国家码')  # 国家代码

    provider = sa.Column(
        sa.Integer, default=SmsProductProvider.NX.value, nullable=False)  # 供应商
    type = sa.Column(
        sa.Integer, default=SmsProductType.VERIFY.value, nullable=False)  # 支持的类型
    price = sa.Column(sa.Numeric(24, 8), default=0,
                      nullable=False, comment='价格')  # 价格
    default_price = sa.Column(sa.Numeric(24, 8), default=0,
                      nullable=False, comment='价格')  # 价格
    user = relationship('User', foreign_keys=[user_id])
    channel = relationship('SmsChannel', foreign_keys=[channel_name])

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'country', 'channel_name'),)

    # 单个号码获取价格和对应产品
    @staticmethod
    def phone_get_price_product(session, user: User, phone: str, sms_type: SmsProductType, channel_name=None) -> (
            str, Decimal, SmsChannel):
        number = phonenumbers.parse("+" + phone)
        country = phonenumbers.region_code_for_number(number)  # 可获取国家名称

        q = session.query(SmsUser).filter(SmsUser.user_id == user.id,
                                          SmsUser.country == country)
        if not channel_name:
            channel_name = user.get_default_channel_name(sms_type)

        if not channel_name:
            sms_product = session.query(SmsProduct).filter(
                SmsProduct.admin_user_id == user.admin_user.id,
                SmsProduct.type == sms_type.value,
                SmsProduct.country == country).order_by(SmsProduct.channel_price.asc()).first()
            channel_name = sms_product.channel_name
        else:
            sms_product = session.query(SmsProduct).filter(
                SmsProduct.admin_user_id == user.admin_user.id,
                SmsProduct.channel_name == channel_name,
                SmsProduct.country == country).first()

        sms_user = q.filter(SmsUser.channel_name == channel_name).first()

        price = sms_user.price
        phone_number = '{}{}'.format(
            number.country_code, number.national_number)
        return phone_number, price, sms_product

    # 通过国家获取价格和对应产品
    @staticmethod
    def country_get_price_product(session, user: User, country_list: list, sms_type: SmsProductType, channel_name=None):
        result_dict = {}

        if not channel_name:
            channel_name = user.get_default_channel_name(sms_type)

        if channel_name:
            for country in country_list:
                sms_product = session.query(SmsProduct).filter(
                    SmsProduct.admin_user_id == user.admin_user.id,
                    SmsProduct.channel_name == channel_name,
                    SmsProduct.country == country).first()

                sms_user = session.query(SmsUser).filter(SmsUser.user_id == user.id,
                                                         SmsUser.channel_name == channel_name,
                                                         SmsUser.country == country).first()
                if sms_product and sms_user:
                    result_dict.update(
                        {country: {'price': sms_user.price, 'product': sms_product}})
        else:
            for country in country_list:
                sms_product = session.query(SmsProduct).filter(
                    SmsProduct.admin_user_id == user.admin_user.id,
                    SmsProduct.type == sms_type.value,
                    SmsProduct.country == country).order_by(SmsProduct.channel_price.asc()).first()
                if not sms_product:
                    continue
                sms_user = session.query(SmsUser).filter(SmsUser.user_id == user.id,
                                                         SmsUser.channel_name == sms_product.channel_name,
                                                         SmsUser.country == country).first()
                if sms_product and sms_user:
                    result_dict.update(
                        {country: {'price': sms_user.price, 'product': sms_product}})
        return result_dict
