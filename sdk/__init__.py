# -*- coding: utf-8 -*-
from enum import Enum


class SmsExceptionEnum(int, Enum):
    CONTENT_MALFORMED = 1000  # 内容格式不对
    CONTENT_TOO_LARGE = 1001  # 内容过长
    CONTENT_IS_EMPTY = 1002  # 内容为空
    CONTENT_ERROR = 1003  # 内容敏感
    NOT_PERMISSION = 1004  # 没权限
    IP_LIMIT = 1005  # IP 限制
    PHONE_TOO_LARGE = 1006  # 号码太多
    PHONE_IS_EMPTY = 1007  # 号码为空
    PHONE_IS_ERROR = 1008  # 号码异常
    BALANCE_LACK = 1009  # 余额不足
    ACCOUNT_LOCK = 1010  # 账号锁定
    SYSTEM_ERROR = 1011  # 系统错误


class SmsStatus(int, Enum):
    """短信状态 0：成功；1：等待；2: 发送中；3：发送失败"""
    SUCCESS = 0
    PENDING = 1
    PROCESS = 2
    FAIL = 3


class SmsDriver:
    send_limit: int
    status_limit: int

    def send_sms(self, phone_list: list, content) -> list:
        pass

    def get_status(self, ids: list) -> list:
        pass


class SmsError(Exception):
    def __init__(self, code: SmsExceptionEnum, message):
        self.code = code
        self.message = message
