# -*- coding: utf-8 -*-
from decimal import Decimal
import hashlib
import logging
import random
import json
import requests

import sqlalchemy as sa

from enum import Enum
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.orm import relationship
from passlib.hash import pbkdf2_sha256
from binascii import b2a_hex, a2b_hex
from Crypto.Cipher import AES

from app.api import BsException, BsExceptionEnum
from app.model import UuidBase, app_config, AutoIncrementBase, generate_timestamp_id
from app.model.pin_code import SmsPinCode, EmailPinCode
from app.model.application import Application
from app.model.contact import ContactGroup
from app.model.admin_user import AdminUserBase
from app.model.sms_product import SmsProductType


class UserRet(int, Enum):
    OK = 0  # 正常

    UID_EXIST = 1  # uid已存在
    UID_INVAILD = 2  # uid无效

    EMAIL_EXIST = 3  # 邮箱错误
    MOBILE_EXIST = 4  # 手机错误

    EMAIL_NOT_MATCH = 5  # 邮箱不匹配
    MOBILE_NOT_MATCH = 6  # 手机不匹配


class UserBase(UuidBase):
    __abstract__ = True

    uid = sa.Column(sa.String(20), unique=True)  # 用户ID

    email = sa.Column(sa.String(50), unique=True, nullable=False)
    country_code = sa.Column(sa.String(16))  # 国际电话区号
    mobile = sa.Column(sa.String(16))  # 手机号
    password = sa.Column(sa.String(256), nullable=False)
    security_password = sa.Column(sa.String(256))  # 安全密码
    locked = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 0 未锁定  1 锁定
    active = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 是否激活: 0 未激活  1 激活
    token = sa.Column(sa.String(256))

    def set_password(self, password):
        self.password = pbkdf2_sha256.encrypt(password, rounds=50000, salt_size=16)

    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.password)

    @property
    def has_security_password(self):
        return 1 if self.security_password else 0

    def set_security_password(self, password):
        self.security_password = pbkdf2_sha256.encrypt(password, rounds=50000, salt_size=16)

    def verify_security_password(self, password):
        if self.security_password is None:
            return True
        return pbkdf2_sha256.verify(password, self.security_password)

    @classmethod
    def reset_password(cls, session, unique_id, pin_code, password):
        # 带有 @ 用 email
        # 首位字符为数字用 mobile
        user = None
        if '@' in unique_id:
            EmailPinCode.flask_check(session, unique_id, pin_code)
            user = session.query(cls).filter_by(email=unique_id).first()
        elif len(unique_id) and unique_id[0].isdigit():
            SmsPinCode.flask_check(session, unique_id, pin_code)
            user = session.query(cls).filter_by(mobile=unique_id).first()
        if user:
            user.set_password(password)
            user.generate_auth_token()
        return user

    @classmethod
    def reset_security_password(cls, session, unique_id, pin_code, password):
        # 带有 @ 用 email
        # 首位字符为数字用 mobile
        user = None
        if '@' in unique_id:
            EmailPinCode.flask_check(session, unique_id, pin_code)
            user = session.query(cls).filter_by(email=unique_id).first()
        elif len(unique_id) and unique_id[0].isdigit():
            SmsPinCode.flask_check(session, unique_id, pin_code)
            user = session.query(cls).filter_by(mobile=unique_id).first()
        if user:
            user.set_security_password(password)
        return user

    def set_uid(self, session):
        if self.uid:
            return
        try_times = 5
        while try_times:
            try_times -= 1
            code = str(random.randint(1000000, 9999999))
            if not session.query(User).filter(User.uid == code).first():
                self.uid = code
                return True

        try_times = 5
        while try_times:
            try_times -= 1
            code = str(random.randint(10000000, 99999999))
            if not session.query(User).filter(User.uid == code).first():
                self.uid = code
                return True

        raise BsException(BsExceptionEnum.USER_UID_EXIST, '用户ID已存在')

    def activate(self, session):

        from app.model.schedule_task import UserRegisterScheduleTask
        self.active = 1
        Application.add_default(session, self.id)
        ContactGroup.add_default(session, self.id)
        task = UserRegisterScheduleTask(user_id=self.id)
        session.add(task)

    @classmethod
    def get_user(cls, session, unique_id):
        # 带有 @ 用 email
        # 首位字符为数字用 mobile
        # 其它用 uid

        user = None
        if '@' in unique_id:
            user = session.query(cls).filter_by(email=unique_id, active=1).first()
        elif len(unique_id) and unique_id[0].isdigit():
            user = session.query(cls).filter_by(mobile=unique_id, active=1).first()
        else:
            user = session.query(cls).filter_by(uid=unique_id).first()

        return user

    def bind_id(self, session, unique_id, pin_code, country_code):
        # 带有 @ 用 email
        # 首位字符为数字用 mobile
        if '@' in unique_id:
            if self.email:
                return UserRet.EMAIL_EXIST
            EmailPinCode.flask_check(session, unique_id, pin_code)
            self.email = unique_id
        elif len(unique_id) and unique_id[0].isdigit():
            if self.mobile:
                return UserRet.MOBILE_EXIST
            SmsPinCode.flask_check(session, unique_id, pin_code)
            self.mobile = unique_id
            self.country_code = country_code

    def rebind_id(self, session, unique_id, pin_code, new_unique_id, new_pin_code, country_code):
        # 带有 @ 用 email
        # 首位字符为数字用 mobile
        if '@' in unique_id:
            if self.email != unique_id:
                return UserRet.EMAIL_NOT_MATCH
            EmailPinCode.flask_check(session, unique_id, pin_code)
            EmailPinCode.flask_check(session, new_unique_id, new_pin_code)
            self.email = new_unique_id
        elif len(unique_id) and unique_id[0].isdigit():
            if self.mobile != unique_id:
                return UserRet.MOBILE_NOT_MATCH
            SmsPinCode.flask_check(session, unique_id, pin_code)
            SmsPinCode.flask_check(session, new_unique_id, new_pin_code)
            self.mobile = new_unique_id
            self.country_code = country_code

    def generate_auth_token(self, verify_again: bool = False, expiration=5 * 24 * 60 * 60):
        if verify_again:
            expiration = 60 * 5
        s = Serializer(app_config.SECRET_KEY, expires_in=expiration)
        self.token = s.dumps({'id': str(self.id), 'verify_again': verify_again})

    @classmethod
    def verify_auth_token(cls, session, token, verify_again=True):
        if not token:
            return None
        s = Serializer(app_config.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = session.query(cls).get(data['id'])
        if verify_again:
            verify_again = data.get('verify_again', True)
        if user and not user.locked and user.token == token and not verify_again:
            return user
        return None


class UserBalanceType(int, Enum):
    """钱包类型 1:基本; 2:冻结; 4:USDT"""
    BASE = 0x0001
    FROZEN = 0x0002
    USDT = 0x0004
    # TOKEN = 0x0002
    # TOKEN_POOL = 0x0004
    # PROFIT = 0x0008


class UserBalanceRecordType(int, Enum):
    """记录类型 1:充值; 2:提现; 4:消费; 8:退款; 16:管理员充值;"""
    RECHARGE = 0x0001  # 充值
    WITHDRAW = 0x0002  # 提现
    CONSUME = 0x0004  # 消费
    REFUND = 0x0008  # 退款
    ADMIN_RECHARGE = 0x0010  # 管理员充值


class UserBalanceRecord(AutoIncrementBase):
    __tablename__ = 'user_balance_record'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)
    other_user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'))  # 被发起者
    type = sa.Column(sa.Integer, nullable=False)  # 钱包类型
    record_type = sa.Column(sa.Integer, nullable=False)  # 记录类型
    current_amount = sa.Column(sa.Numeric(24, 8), nullable=False)  # 当前量
    delta_amount = sa.Column(sa.Numeric(24, 8), nullable=False)  # 变化量
    details = sa.Column(sa.Text, nullable=False)  # 详情

    user = relationship('User', foreign_keys=[user_id])
    other_user = relationship('User', foreign_keys=[other_user_id])

    @property
    def details_json(self):
        return json.loads(self.details)


class UserLoginRecord(AutoIncrementBase):
    __tablename__ = 'user_login_record'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)
    login_status = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 登录状态 0：未登录 1：登录

    user = relationship('User', foreign_keys=[user_id])


class User(UserBase):
    __tablename__ = 'user'

    VIRTUAL_ID = '00000000-0000-0000-0000-000000000000'

    admin_user_id = sa.Column(sa.String(36), sa.ForeignKey('admin_user.id'), nullable=False)

    name = sa.Column(sa.String(60))
    first_name = sa.Column(sa.String(60))
    last_name = sa.Column(sa.String(60))
    nickname = sa.Column(sa.String(60))
    # authy_id = sa.Column(sa.String(16), unique=True)  # authy ID
    # status_2FA = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 是否开启二次验证 0 关闭  1 安全密码  2 手机验证码  3 app 验证码
    # extra = sa.Column(sa.Text)  # 扩展字段
    avatar = sa.Column(sa.String(256))

    status_2FA = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 否开启二次验证 0 关闭  1开启

    usdt_number = sa.Column(sa.String(16), default=generate_timestamp_id, unique=True)
    usdt_address = sa.Column(sa.String(128), unique=True)  # usdt 充值地址
    usdt_recharge = sa.Column(sa.Numeric(24, 8), default=0)  # 充值
    usdt_balance = sa.Column(sa.Numeric(24, 8), default=0)  # 钱包(USDT数量)

    balance = sa.Column(sa.Numeric(24, 2), default=0)  # 余额

    frozen_balance = sa.Column(sa.Numeric(24, 8), default=0)  # 冻结余额

    # relationship
    admin_user = relationship('AdminUser', foreign_keys=[admin_user_id])
    default_sms_channel_name = sa.Column(sa.String(50), nullable=True)
    default_verify_channel_name = sa.Column(sa.String(50), nullable=True)

    @staticmethod
    def check_sign(data, app_id, app_key):
        signature = data.pop('signature')
        data['app_id'] = app_id
        data['app_key'] = app_key
        items = data.items()
        kv_pair_list = []
        for k, v in items:
            kv_pair_list.append('{}={}'.format(k, v))
        kv_pair_list.sort()
        signature_content = '&'.join(kv_pair_list).encode('utf-8')
        expected_signature = hashlib.md5(signature_content).hexdigest()
        if expected_signature != signature:
            logging.warning('Signature for %s not match. %s presented but expect %s', signature_content, signature,
                            expected_signature)
            raise BsException(BsExceptionEnum.CHECK_SIGN_ERROR, '检查签名失败')

    def get_default_channel_name(self, sms_type: SmsProductType) -> str:
        if sms_type == SmsProductType.VERIFY:
            return self.default_verify_channel_name
        else:
            return self.default_sms_channel_name

    def create_address(self, currency_code, number):
        data = {'number': number,
                'currency_code': currency_code,
                'erc20_token': 1,
                'amount': str(0),
                'notify_url': app_config.DIZPAY_CALL_BACK,
                'app_key': app_config.APP_KEY,
                'app_id': app_config.APP_ID}
        items = data.items()
        kv_pair_list = []
        for k, v in items:
            kv_pair_list.append('{}={}'.format(k, v))
        kv_pair_list.sort()
        signature_content = '&'.join(kv_pair_list).encode('utf-8')
        signature = hashlib.md5(signature_content).hexdigest()
        data.pop('app_key')
        data['signature'] = signature
        r = requests.post(app_config.DIZPAY_CREATE_CHARGE_ORDER,
                          json=data, timeout=100)
        if r.status_code == requests.codes.ok:
            if r.encoding is None or r.encoding == 'ISO-8859-1':
                r.encoding = 'UTF-8'
            return r.json().get('to_address')
        else:
            raise BsException(BsExceptionEnum.DIZPAY_ERROR, r.text)

    @staticmethod
    def initialize(session):
        virtual_user = session.query(User).get(User.VIRTUAL_ID)
        if virtual_user is None:
            # 生成虚拟用户
            virtual_user = User(id=User.VIRTUAL_ID,
                                uid='888888',
                                email='user@icai.com',
                                mobile='13800000000',
                                admin_user_id=AdminUserBase.ROOT_ID)
            virtual_user.set_password('888888')
            virtual_user.set_security_password('888888')
            virtual_user.generate_auth_token()
            session.add(virtual_user)
            session.flush()
            virtual_user.activate(session)

            session.commit()

    def update_balance(self,
                       session,
                       type: UserBalanceType,
                       amount: Decimal,
                       record_type: UserBalanceRecordType,
                       details={},
                       other_user_id=None):
        if type == UserBalanceType.BASE:
            ret = session.query(User).filter(User.id == self.id, User.balance >= -amount).update(
                dict(balance=User.balance + amount))
            balance = self.balance
        elif type == UserBalanceType.FROZEN:
            ret = session.query(User).filter(User.id == self.id, User.frozen_balance >= -amount).update(
                dict(frozen_balance=User.frozen_balance + amount))
            return True if ret == 1 else False
        elif type == UserBalanceType.USDT:
            # ret = session.query(User).filter(User.id == self.id, User.usdt_balance >= -amount).update(
            #     dict(usdt_balance=User.usdt_balance + amount))
            # balance = self.usdt_balance
            ret = session.query(User).filter(User.id == self.id, User.balance >= -amount).update(
                dict(balance=User.balance + amount))
            balance = self.balance
        # elif type == UserBalanceType.TOKEN:
        #     ret = session.query(User).filter(User.id == self.id, User.token_balance >= -amount).update(
        #         dict(token_balance=User.token_balance + amount))
        #     balance = self.token_balance
        # elif type == UserBalanceType.TOKEN_POOL:
        #     ret = session.query(User).filter(User.id == self.id, User.token_pool_balance >= -amount).update(
        #         dict(token_pool_balance=User.token_pool_balance + amount))
        #     balance = self.token_pool_balance
        # elif type == UserBalanceType.PROFIT:
        #     ret = session.query(User).filter(User.id == self.id, User.profit_balance >= -amount).update(
        #         dict(profit_balance=User.profit_balance + amount))
        #     balance = self.profit_balance
        else:
            return False

        if ret == 1:
            record = UserBalanceRecord(user_id=self.id,
                                       other_user_id=other_user_id,
                                       type=type.value,
                                       record_type=record_type.value,
                                       current_amount=balance,
                                       delta_amount=amount,
                                       details=json.dumps(details))

            session.add(record)
            session.flush()
            return True
        return False
