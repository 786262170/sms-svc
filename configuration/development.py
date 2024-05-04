# -*- coding: utf-8 -*-
import os


class DevelopmentConfig(object):
    DEBUG = True

    DEBUG_API = True

    LOG_LEVEL = 'DEBUG'

    SECRET_KEY = 'e2G6RaumKIv5iHPnYrFDLIiURrY1jjU9jkkrkySTCh79sL7D5q8mC26JaotUofHH'

    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URL = 'mysql://root:root123456@127.0.0.1:3306/icaisms?charset=utf8mb4'
    # SQLALCHEMY_DATABASE_URL = 'mysql://root:zCLZpdZD3DrwqG2!@134.175.97.227:3306/icaisms?charset=utf8mb4'
    # SQLALCHEMY_DATABASE_URL = 'mysql://icaicloud:9o4&^ZCLY05c@127.0.0.1:33062/icaisms-api?charset=utf8mb4'

    SQLALCHEMY_POOL_RECYCLE = 7200
    SQLALCHEMY_POOL_SIZE = 10

    TIMEZONE = 'Asia/Shanghai'

    KEY = 'carlzhuangzhao12'

    PRODUCT_NAME = 'icaisms-api-dev'

    DIZPAY_QUERY_CURRENCY = 'https://api.dizpay.com/v2/member/rates/currency'

    EMAIL_FROM_ADDRESS = '财信<no-reply@cmessages.com>'

    EMAIL_API_URL = 'https://icaimail-api.staging.icaicloud.com/mail/send'

    EMAIL_API_SECRET = 'n8bW3nymDzsYv0vsnKfCcGiGR'

    EMAIL_RESET_PASSWORD = "https://icaisms-dashboard.staging.icaicloud.com/#/reset?email={email}&code={code}"
    EMAIL_RESET_PASSWORD_TITLE = "Reset your password"
    EMAIL_RESET_PASSWORD_TEMPLATE = 'cmessages-confirm-reset'

    EMAIL_ACTIVE_ACCOUNT = "https://icaisms-dashboard.staging.icaicloud.com/#/login?email={email}&code={code}"
    EMAIL_ACTIVE_TEMPLATE = 'cmessages-confirm-email'
    EMAIL_ACTIVE_MAIL_TITLE = "Your Account is almost ready"

    EMAIL_PIN_CODE_MAIL_TITLE = 'Your CMessages Pin Code'
    EMAIL_PIN_CODE_MAIL_TEMPLATE = 'cmessages-code'