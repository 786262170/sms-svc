# -*- coding: utf-8 -*-
from typing import List
from decimal import Decimal

import time
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session

from app.api import PaginateBase, OrmBaseModel, get_db, BsException, BsExceptionEnum, GetSession
from app.api.member import member_login_required
from app.model import timestamp_to_datetime
from app.model.wallet_order import WalletOrder, WalletOrderPaymentType, WalletOrderStatus

router = APIRouter()


class UserResponse(OrmBaseModel):
    id: str
    uid: str
    avatar: str = None
    nickname: str = None
    name: str = None
    # gender: UserGender = Field(UserGender.NOT_CHOICE, description=enum_to_json(UserGender))
    active: int
    # usdt_balance: Decimal = Field(..., description='usdt 金额')


class WalletOrderResponse(OrmBaseModel):
    id: int
    created_timestamp: int

    amount: Decimal = Field(..., description='金额')

    payment_type: WalletOrderPaymentType = Field(..., description=WalletOrderPaymentType.__doc__)

    card_number: str = Field(None, description='卡号')
    wechat: str = Field(None, description='微信')
    alipay: str = Field(None, description='支付宝')
    address: str = Field(None, description='usdt地址')

    image: str = Field(None, description='支付凭证')
    remark: str = Field(None, description='备注')

    status: WalletOrderStatus = Field(..., description=WalletOrderStatus.__doc__)

    user: UserResponse


class WalletOrderList(PaginateBase):
    items: List[WalletOrderResponse] = []


@router.get('/list', response_model=WalletOrderList)
def wallet_order_list(page: int = 1,
                      per_page: int = 5,
                      payment_type: int = None,
                      order_status: int = None,
                      created_begin_timestamp: int = None,
                      created_end_timestamp: int = None,
                      current_user=Depends(member_login_required),
                      session: Session = Depends(get_db)):
    """钱包订单列表"""
    q = session.query(WalletOrder)
    q = q.filter(WalletOrder.user_id == current_user.id)
    if payment_type is not None:
        q = q.filter(WalletOrder.payment_type.op('&')(payment_type))
    if order_status is not None:
        q = q.filter(WalletOrder.status.op('&')(order_status))

    if created_begin_timestamp:
        if not created_end_timestamp:
            created_end_timestamp = int(time.time())
        begin_timestamp = min(created_begin_timestamp, created_end_timestamp)
        end_timestamp = max(created_begin_timestamp, created_end_timestamp)
        q = q.filter(sa.and_(WalletOrder.created_at >= timestamp_to_datetime(begin_timestamp),
                             WalletOrder.created_at < timestamp_to_datetime(end_timestamp)))

    q = q.order_by(WalletOrder.id.desc())
    return q.paginate(page, per_page)


@router.get('/details/{order_id}', response_model=WalletOrderResponse)
def wallet_order_detail(order_id: int,
                        session: Session = Depends(GetSession(member_login_required))):
    """钱包订单详情"""
    current_user = session.info['current_user']
    order = session.query(WalletOrder).filter(WalletOrder.id == order_id,
                                              WalletOrder.user_id == current_user.id).first()
    if not order:
        raise BsException(BsExceptionEnum.WALLET_ORDER_NOT_EXIST, '钱包订单不存在')
    return order


class WalletOrderRequest(BaseModel):
    amount: str = Field(..., description='金额')

    payment_type: WalletOrderPaymentType = Field(..., description='支付类型')

    card_number: str = Field(None, description='卡号')
    wechat: str = Field(None, description='微信')
    alipay: str = Field(None, description='支付宝')
    address: str = Field(None, description='usdt地址')

    image: str = Field(..., description='支付凭证')
    remark: str = Field(None, description='备注')


@router.post('/create', response_model=WalletOrderResponse)
def wallet_order_create(data: WalletOrderRequest,
                        session: Session = Depends(GetSession(member_login_required))):
    """钱包订单创建"""
    current_user = session.info['current_user']

    if data.payment_type == WalletOrderPaymentType.BANK:
        if data.card_number is None:
            raise BsException(BsExceptionEnum.PARAMETER_ERROR, '无效参数')
    elif data.payment_type == WalletOrderPaymentType.WECHAT:
        if data.wechat is None:
            raise BsException(BsExceptionEnum.PARAMETER_ERROR, '无效参数')
    elif data.payment_type == WalletOrderPaymentType.ALIPAY:
        if data.alipay is None:
            raise BsException(BsExceptionEnum.PARAMETER_ERROR, '无效参数')
    elif data.payment_type == WalletOrderPaymentType.USDT:
        pass
    else:
        raise BsException(BsExceptionEnum.PARAMETER_ERROR, '无效参数')

    order = WalletOrder(user_id=current_user.id,
                        amount=data.amount,
                        payment_type=data.payment_type.value,
                        card_number=data.card_number,
                        wechat=data.wechat,
                        alipay=data.alipay,
                        address=data.address,
                        image=data.image,
                        remark=data.remark)

    session.add(order)
    session.commit()
    return order


class WalletOrderStatusRequest(BaseModel):
    status: WalletOrderStatus = Field(..., description='状态')


@router.put('/details/{order_id}', response_model=WalletOrderResponse)
def wallet_order_modify(order_id: int,
                        data: WalletOrderStatusRequest,
                        session: Session = Depends(GetSession(member_login_required))):
    """钱包订单修改"""
    current_user = session.info['current_user']
    order = session.query(WalletOrder).filter(WalletOrder.user_id == current_user.id,
                                              WalletOrder.id == order_id).first()
    if not order:
        raise BsException(BsExceptionEnum.WALLET_ORDER_NOT_EXIST, '订单不存在')

    if data.status is not None and data.status != WalletOrderStatus.CANCEL:
        raise BsException(BsExceptionEnum.WALLET_ORDER_STATUS_ERR, '钱包订单状态错误')

    ret = session.query(WalletOrder).filter(
        WalletOrder.user_id == current_user.id, WalletOrder.id == order_id,
        WalletOrder.status == WalletOrderStatus.PENDING.value).update(dict(status=data.status.value))
    if ret != 1:
        raise BsException(BsExceptionEnum.MESSAGE_TEMPLATE_STATUS_ERR, '消息模板状态错误')

    session.commit()
    return order
