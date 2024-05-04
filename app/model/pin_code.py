# -*- coding: utf-8 -*-
import datetime

import sqlalchemy as sa
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired

from app.api import BsException, BsExceptionEnum
from app.model import Base, app_config


class PinCodeBase(Base):
    __abstract__ = True

    created_at = sa.Column(sa.DateTime,
                           default=datetime.datetime.utcnow,
                           nullable=False)
    updated_at = sa.Column(sa.DateTime,
                           default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow,
                           nullable=False)
    pin_code_signature = sa.Column(sa.String(256), nullable=False)
    try_times = sa.Column(sa.SmallInteger, default=0)

    def generate_signature(self, session, pin_code, expiration=30 * 60):
        s = Serializer(app_config.SECRET_KEY, expires_in=expiration)
        self.pin_code_signature = s.dumps({'id': pin_code})
        self.try_times = 0
        session.add(self)
        session.commit()

    # 返回值
    #   0 成功
    #   1 尝试次数太多
    #   2 PIN码错误
    #   3 PIN码过期
    @classmethod
    def verify(cls, session, unique_id, pin_code):
        result = session.query(cls).get(unique_id)
        if result is None:
            return 2
        result.try_times = result.try_times + 1
        session.commit()
        if result.try_times > 5:
            return 1
        s = Serializer(app_config.SECRET_KEY)
        try:
            data = s.loads(result.pin_code_signature)
        except SignatureExpired:
            return 3  # valid signature, but expired
        except BadSignature:
            return 2  # invalid signature
        if data['id'] == pin_code.lower():
            session.delete(result)
            session.commit()
            return 0
        return 2


class CaptchaPinCode(PinCodeBase):
    __tablename__ = 'captcha_pin_code'

    id = sa.Column(sa.String(36), primary_key=True)

    @classmethod
    def flask_check(cls, session, unique_id, pin_code):
        result = cls.verify(session, unique_id, pin_code)
        if result == 1:
            raise BsException(BsExceptionEnum.CAPTCHA_PIN_CODE_MANY_TIMES, 'try too many times')
        elif result == 2:
            raise BsException(BsExceptionEnum.CAPTCHA_PIN_CODE_NOT_MATCH, 'pin code does not match')
        elif result == 3:
            raise BsException(BsExceptionEnum.CAPTCHA_PIN_CODE_EXPIRED, 'pin code is expired')


class SmsPinCode(PinCodeBase):
    __tablename__ = 'sms_pin_code'

    id = sa.Column(sa.String(11), primary_key=True)

    @classmethod
    def flask_check(cls, session, unique_id, pin_code):
        result = cls.verify(session, unique_id, pin_code)
        if result == 1:
            raise BsException(BsExceptionEnum.SMS_PIN_CODE_MANY_TIMES, 'try too many times')
        elif result == 2:
            raise BsException(BsExceptionEnum.SMS_PIN_CODE_NOT_MATCH, 'pin code does not match')
        elif result == 3:
            raise BsException(BsExceptionEnum.SMS_PIN_CODE_EXPIRED, 'pin code is expired')


class EmailPinCode(PinCodeBase):
    __tablename__ = 'email_pin_code'

    id = sa.Column(sa.String(60), primary_key=True)

    @classmethod
    def flask_check(cls, session, unique_id, pin_code):
        result = cls.verify(session, unique_id, pin_code)
        if result == 1:
            raise BsException(BsExceptionEnum.EMAIL_PIN_CODE_MANY_TIMES, 'try too many times')
        elif result == 2:
            raise BsException(BsExceptionEnum.EMAIL_PIN_CODE_NOT_MATCH, 'pin code does not match')
        elif result == 3:
            raise BsException(BsExceptionEnum.EMAIL_PIN_CODE_EXPIRED, 'pin code is expired')

