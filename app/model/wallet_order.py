# -*- coding: utf-8 -*-
import sqlalchemy as sa

from enum import Enum
from sqlalchemy.orm import relationship
from app.model import AutoIncrementBase


class WalletOrderStatus(int, Enum):
    """订单状态 1:待审核；2:成功；4:失败；8:驳回；16:取消"""
    PENDING = 1
    SUCCESS = 2
    FAIL = 4
    REJECT = 8
    CANCEL = 16


class WalletOrderPaymentType(int, Enum):
    """支付类型 1:银行卡；2:微信；4:支付宝；8:USDT；"""
    BANK = 1  # 银行卡
    WECHAT = 2  # 微信
    ALIPAY = 4  # 支付宝
    USDT = 8  # USDT


class WalletOrder(AutoIncrementBase):
    __tablename__ = 'wallet_order'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)

    amount = sa.Column(sa.Numeric(24, 8), default=0, nullable=False)  # 金额

    payment_type = sa.Column(sa.SmallInteger, nullable=False)  # 支付类型

    card_number = sa.Column(sa.String(64))  # 卡号
    wechat = sa.Column(sa.String(64))  # 微信
    alipay = sa.Column(sa.String(64))  # 支付宝
    address = sa.Column(sa.String(64))  # usdt 地址

    image = sa.Column(sa.String(512), default='')  # 支付凭证
    remark = sa.Column(sa.String(64), default='')  # 备注

    status = sa.Column(sa.SmallInteger, default=WalletOrderStatus.PENDING.value)  # 订单状态

    # relationship
    user = relationship('User', foreign_keys=[user_id])

