# -*- coding: utf-8 -*-
import random

from enum import Enum
import sqlalchemy as sa

from binascii import b2a_hex, a2b_hex
from Crypto.Cipher import AES
from sqlalchemy.orm import relationship

from app.api import BsException, BsExceptionEnum
from app.model import app_config, BaseModel

class ApplicationCategory(int, Enum):
    '''来自需求文档:
    RUMMY = 1
    CASINO = 2
    PAYDAY_LOAN = 3
    MT4 = 4
    BINARY_OPTION = 5
    CYRPTO = 6
    EARNINGS = 7
    ECOMMERCE = 8
    '''
    INVALID=0
    RUMMY = 1
    CASINO = 2
    PAYDAY_LOAN = 3
    MT4 = 4
    BINARY_OPTION = 5
    CYRPTO = 6
    EARNINGS = 7
    ECOMMERCE = 8

class Application(BaseModel):
    __tablename__ = 'application'

    APPLICATION_NAME_DEFAULT = 'default'

    app_id = sa.Column(sa.String(18), primary_key=True)
    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False)

    name = sa.Column(sa.String(60), nullable=False)

    _app_key = sa.Column('app_key', sa.String(128), nullable=False)
    # secret_key = sa.Column(sa.String(128), nullable=False)

    sms_hook_url = sa.Column(sa.String(256))  # sms失败回调的 url

    invalid = sa.Column(sa.Integer, default=0, nullable=False)  # 0为有效 1为无效

    user = relationship('User', foreign_keys=[user_id])
    
    country = sa.Column(sa.String(60)) # 国家

    link = sa.Column(sa.String(200)) # GP链接

    remark = sa.Column(sa.String(200)) # 备注

    category = sa.Column(sa.Integer, default=ApplicationCategory.RUMMY.value, nullable=False) # 行业分类    

    def set_app_id(self, session):
        if self.app_id:
            return
        try_times = 5
        while try_times:
            try_times -= 1
            app_id = 'dp' + ''.join(random.sample('abcdedfhkmnpqrtuvwxy2346789ABCDEFGHKLMNPQRTUVWXY2346789', 16))
            if not session.query(Application).filter(Application.app_id == app_id).first():
                self.app_id = app_id
                return True

        raise BsException(BsExceptionEnum.APP_ID_EXIST, '应用ID已存在')

    @staticmethod
    def generate_app_key():
        text = ''.join(random.sample('abcdedfhkmnpqrtuvwxy2346789ABCDEFGHKLMNPQRTUVWXY2346789', 32))
        cryptor = AES.new(str.encode(app_config.KEY), AES.MODE_CBC, b'0000000000000000')
        length = 16
        text = text.encode('utf-8')
        count = len(text)
        if count < length:
            add = (length - count)
            # \0 backspace
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        elif count > length:
            add = (length - (count % length))
            # text = text + ('\0' * add)
            text = text + ('\0' * add).encode('utf-8')
        ciphertext = cryptor.encrypt(text)
        return b2a_hex(ciphertext)

    @staticmethod
    def query_app_key(text):
        cryptor = AES.new(str.encode(app_config.KEY), AES.MODE_CBC, b'0000000000000000')
        plain_text = cryptor.decrypt(a2b_hex(text))
        return plain_text.rstrip(b'\0').decode('utf-8')

    @property
    def app_key(self):
        return self.query_app_key(self._app_key)

    @staticmethod
    def create(session, user_id, name, sms_hook_url=None):
        app = Application(name=name,
                          _app_key=Application.generate_app_key(),
                          # secret_key=Application.generate_app_key(),
                          user_id=user_id,
                          sms_hook_url=sms_hook_url)
        app.set_app_id(session)
        session.add(app)
        session.flush()

        return app

    @staticmethod
    def add_default(session, user_id):
        Application.create(session, user_id, Application.APPLICATION_NAME_DEFAULT)

    @staticmethod
    def default_get(session, user_id):
        return session.query(Application).filter(Application.user_id == user_id,
                                                 Application.name == Application.APPLICATION_NAME_DEFAULT).first()
