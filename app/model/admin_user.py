# -*- coding: utf-8 -*-
import json
import random
from enum import Enum

import sqlalchemy as sa
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.hash import pbkdf2_sha256
from sqlalchemy import inspect
from sqlalchemy.orm import relationship

from app.api import BsException, BsExceptionEnum
from app.model import UuidBase, AutoIncrementBase, app_config
from app.model.message import MessageCheck
from app.model.sms_product import SmsProduct


class AdminUserRole(int, Enum):
    SUPER = 0x0001  # 超级管理员
    FINANCE = 0x0002  # 财务管理员
    CSR = 0x0004  # 客服
    FIRST_AGENT = 0x0008  # 一级代理（合作代理）

    ALL_ROLE = SUPER | FINANCE | CSR | FIRST_AGENT
    ALL_AGENT = FIRST_AGENT


class AdminUserBase(UuidBase):
    __abstract__ = True

    ROOT_ID = '00000000-0000-0000-0000-000000000000'

    uid = sa.Column(sa.String(20), unique=True, nullable=False)
    code = sa.Column(sa.String(20), unique=True)  # 推荐码
    password = sa.Column(sa.String(256), nullable=False)
    security_password = sa.Column(sa.String(256))
    role = sa.Column(sa.SmallInteger, default=AdminUserRole.FIRST_AGENT.value, nullable=False)
    locked = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 0 未锁定  1 锁定
    active = sa.Column(sa.SmallInteger, default=0, nullable=False)  # 是否激活: 0 未激活  1 激活
    token = sa.Column(sa.String(256))
    permission = sa.Column(sa.Text, default='{}')  # 权限

    @property
    def permission_json(self):
        return json.loads(self.permission)

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

    def generate_auth_token(self, expiration=5 * 24 * 60 * 60):
        s = Serializer(app_config.SECRET_KEY, expires_in=expiration)
        self.token = s.dumps({'id': str(self.id)})

    @classmethod
    def verify_auth_token(cls, session, token):
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
        if user and not user.locked and user.token == token:
            return user
        return None

    def activate(self, session):
        from app.model.schedule_task import AdminRegisterScheduleTask
        self.active = 1
        task = AdminRegisterScheduleTask(admin_user_id=self.id)
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

    def set_code(self):
        session = inspect(self).session
        if self.code:
            return
        try_times = 5
        while try_times:
            try_times -= 1
            code = str(random.randint(100000, 999999))
            if not session.query(AdminUser).filter(AdminUser.code == code).first():
                self.code = code
                return True

        try_times = 5
        while try_times:
            try_times -= 1
            code = str(random.randint(10000000, 99999999))
            if not session.query(AdminUser).filter(AdminUser.code == code).first():
                self.code = code
                return True

        raise BsException(BsExceptionEnum.SPONSOR_CODE_EXIST, 'code already exists')


class AdminUserBalanceRecordType(int, Enum):
    """记录类型 1:收益; 2:提现;"""
    PROFIT = 0x0001  # 收益
    WITHDRAW = 0x0002  # 提现


class AdminUserBalanceRecord(AutoIncrementBase):
    __tablename__ = 'admin_user_balance_record'

    admin_id = sa.Column(sa.String(36), sa.ForeignKey('admin_user.id'), nullable=False)
    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)
    sms_check_id = sa.Column(sa.Integer, sa.ForeignKey('message_check.id'))
    record_type = sa.Column(sa.Integer, nullable=False)  # 记录类型
    current_amount = sa.Column(sa.Numeric(24, 8), nullable=False)  # 当前量
    delta_amount = sa.Column(sa.Numeric(24, 8), nullable=False)  # 变化量
    details = sa.Column(sa.Text, nullable=False)  # 详情
    type = sa.Column(sa.Integer, nullable=False)

    admin = relationship('AdminUser', foreign_keys=[admin_id])
    user = relationship('User', foreign_keys=[user_id])
    message_check = relationship('MessageCheck', foreign_keys=[sms_check_id])

    @property
    def details_json(self):
        return json.loads(self.details)


class AdminUser(AdminUserBase):
    __tablename__ = 'admin_user'

    parent_id = sa.Column(sa.String(36), sa.ForeignKey('admin_user.id'))
    email = sa.Column(sa.String(50), unique=True)
    avatar = sa.Column(sa.String(128))
    name = sa.Column(sa.String(60))

    country_code = sa.Column(sa.String(16))  # 国际电话区号
    mobile = sa.Column(sa.String(16), unique=True)  # 手机号

    balance = sa.Column(sa.Numeric(24, 8), default=0, nullable=False)  # 余额-收益

    parent = relationship('AdminUser', foreign_keys=[parent_id], remote_side="AdminUser.id")

    @staticmethod
    def initialize(session):
        root_admin = session.query(AdminUser).get(AdminUserBase.ROOT_ID)
        if root_admin is None:
            root_admin = AdminUser(id=AdminUserBase.ROOT_ID,
                                   uid='admin',
                                   email='admin@icai.com',
                                   mobile='13288888888',
                                   role=AdminUserRole.SUPER.value)
            session.add(root_admin)
            root_admin.set_password('888888')
            root_admin.set_security_password('888888')
            session.flush()
            root_admin.activate(session)
            root_admin.set_code()
            root_admin.generate_auth_token()
            session.commit()

    @staticmethod
    def team_id(session, user):
        team_list = [user.id]
        current_team = session.query(AdminUser.id).filter(AdminUser.parent_id == user.id).all()
        team_list += [x.id for x in current_team]
        while current_team:
            current_team = session.query(AdminUser.id).filter(
                AdminUser.parent_id.in_([x.id for x in current_team])).all()
            team_list += [x.id for x in current_team]
        return team_list

    def update_balance(self,
                       amount,
                       record_type: AdminUserBalanceRecordType,
                       sms_check_id=None,
                       user_id=None,
                       smsProducttype=None,
                       details={}):
        session = inspect(self).session
        ret = session.query(AdminUser).filter(AdminUser.id == self.id, AdminUser.balance >= -amount).update(
            dict(balance=AdminUser.balance + amount))

        if ret == 1:
            record = AdminUserBalanceRecord(admin_id=self.id,
                                            sms_check_id=sms_check_id,
                                            record_type=record_type.value,
                                            current_amount=self.balance,
                                            delta_amount=amount,
                                            details=json.dumps(details),
                                            user_id=user_id,
                                            type=smsProducttype)

            session.add(record)
            session.flush()
            return True
        return False

    @staticmethod
    def update_profit(sms_check: MessageCheck):
        session = inspect(sms_check).session

        price = sms_check.price
        parent: AdminUser = sms_check.sms_product.admin_user
        sms_product: SmsProduct = sms_check.sms_product
        while sms_product:

            profit_amount = price - sms_product.cost_price
            if profit_amount > 0:
                parent.update_balance(profit_amount, AdminUserBalanceRecordType.PROFIT, sms_check.id,sms_check.user_id,sms_product.type)

            price = sms_product.cost_price
            parent = parent.parent
            if not parent:
                break

            sms_product = session.query(SmsProduct).filter(SmsProduct.admin_user_id == parent.id,
                                                           SmsProduct.country == sms_product.country,
                                                           SmsProduct.channel_name == sms_product.channel_name).first()
