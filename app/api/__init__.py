# -*- coding: utf-8 -*-
from typing import List
from pydantic import BaseModel, Field
from starlette.requests import Request
from enum import Enum

from configuration import load_config


class BsExceptionEnum(int, Enum):
    INTERNAL = 1000
    API_BALANCE_NOT_ENOUGH = 1009  # 余额不足

    PARAMETER_ERROR = 4000  # 请求参数错误

    CAPTCHA_PIN_CODE_MANY_TIMES = 4001  # 图片验证码错误太多次
    CAPTCHA_PIN_CODE_NOT_MATCH = 4002  # 图片验证码错误
    CAPTCHA_PIN_CODE_EXPIRED = 4003  # 图片验证码过期

    SMS_PIN_CODE_NOT_MATCH = 4004  # 手机验证码错误
    SMS_PIN_CODE_MANY_TIMES = 4005  # 用户手机验证码尝试次数过多
    SMS_PIN_CODE_EXPIRED = 4006  # 手机验证码失效

    EMAIL_PIN_CODE_NOT_MATCH = 4007  # 邮件验证码错误
    EMAIL_PIN_CODE_MANY_TIMES = 4008  # 邮件验证码尝试次数过多
    EMAIL_PIN_CODE_EXPIRED = 4009  # 邮件验证码失效

    PASSWORD_NOT_MATCH = 4010  # 密码错误
    EMAIL_EXIST = 4011  # 邮箱已存在
    USER_NOT_EXIST = 4012  # 用户不存在
    USER_LOCKED = 4013  # 用户已被锁定
    USER_UID_EXIST = 4014  # 用户UID已经存在
    USER_NOT_ACTIVE = 4015  # 用户未激活
    PERMISSION_NOT_ALLOW = 4016  # 权限不允许
    RECORD_NOT_EXIST = 4017  # 记录不存在
    MOBILE_NOT_EXIST = 4018  # 手机号不存在
    COUNTRY_CODE_NOT_EXIST = 4019  # 区号不存在

    DIZPAY_ERROR = 4020  # 地址生成失败
    CURRENCY_NOT_EXIST = 4021  # 法币类型不存在
    CHECK_SIGN_ERROR = 4022  # 检查签名失败
    BALANCE_NOT_ENOUGH = 4023  # 余额不足

    APP_ID_EXIST = 4024  # 应用ID已经存在
    APP_NOT_EXIST = 4025  # 应用不存在
    APP_NAME_NOT_EXIST = 4026  # 应用名称不存在

    CONTACT_EXIST = 4027  # 联系人已经存在
    CONTACT_NOT_EXIST = 4028  # 联系人不存在

    MESSAGE_TEMPLATE_EXIST = 4029  # 消息模板已经存在
    MESSAGE_TEMPLATE_NOT_EXIST = 4030  # 消息模板不存在
    MESSAGE_TEMPLATE_STATUS_ERR = 4031  # 消息模板状态错误
    MESSAGE_TEMPLATE_CONTENT_EMPTY = 4032  # 消息模板内容为空

    MESSAGE_EXIST = 4033  # 消息已经存在
    MESSAGE_NOT_EXIST = 4034  # 消息不存在
    MESSAGE_CONTENT_EMPTY = 4035  # 消息内容为空

    MESSAGE_CHECK_EXIST = 4036  # 消息检查已经存在
    MESSAGE_CHECK_NOT_EXIST = 4037  # 消息检查不存在

    WALLET_ORDER_EXIST = 4038  # 钱包订单已经存在
    WALLET_ORDER_NOT_EXIST = 4039  # 钱包订单已经存在
    WALLET_ORDER_STATUS_ERR = 4040  # 钱包订单状态错误

    PRODUCT_EXIST = 4041  # 产品已经存在
    PRODUCT_NOT_EXIST = 4042  # 产品不存在

    SPONSOR_CODE_EXIST = 4043  # 推荐码
    SPONSOR_CODE_NOT_EXIST = 4044  # 推荐码不存在

    EMAIL_SEND_ERROR = 4045  # 邮件发送失败
    MESSAGE_SEND_ERROR = 4046  # 消息发送失败

    GROUP_EXIST = 4047  # 分组已经存在
    GROUP_NOT_EXIST = 4048  # 组不存在

    MOBILE_ERROR = 4049  # 手机号错误

    PRICE_TOO_LOW = 4050  # 价格设置太低
    
    TOO_MANY_MOBILE = 4051

class BsException(Exception):
    def __init__(self, code: BsExceptionEnum, message: str):
        self.code = code
        self.message = message


class BsExceptionWithNumbers(BsException):
    numbers: List[str]

    def __init__(self, code: BsExceptionEnum, message: str, numbers: List[str]):
        super().__init__(code, message)
        self.numbers = numbers


class GetSession:
    def __init__(self, login_required=None, role=None):
        self.login_required = login_required
        self.role = role

    def __call__(self, request: Request):
        if self.login_required:
            if self.role:
                current_user = self.login_required(request, self.role)
            else:
                current_user = self.login_required(request)
            request.state.db.info['current_user'] = current_user
        return request.state.db


def get_db(request: Request):
    return request.state.db


def enum_to_json(enum_obj):
    import json
    return json.dumps({i.name: i.value for i in enum_obj})


async def get_request_data(request: Request):
    body = await request.body()
    return body


app_config = load_config()


class OrmBaseModel(BaseModel):
    class Config:
        orm_mode = True


class PaginateBase(OrmBaseModel):
    page: int = Field(..., description='当前页码')
    pages: int = Field(..., description='总页数')
    per_page: int = Field(..., description='每页数量')
    total: int = Field(..., description='总数量')
