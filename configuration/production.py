# -*- coding: utf-8 -*-
from configuration.development import DevelopmentConfig


class ProductionConfig(DevelopmentConfig):
    DEBUG = False

    DEBUG_API = False

    LOG_LEVEL = 'INFO'

    PRODUCT_NAME = 'icaisms-api'

    SQLALCHEMY_ECHO = False

    # SQLALCHEMY_DATABASE_URL = 'mysql://icaicloud:9o4&^ZCLY05c@icaicloud-prod-cluster.cluster-c9650aehmgko.ap-southeast-1.rds.amazonaws.com:3306/opp?charset=utf8mb4'

    DIZPAY_CALL_BACK = 'https://XXX/member/wallet/recharge'
    DIZPAY_CREATE_CHARGE_ORDER = 'https://api.dizpay.com/v2/member/orders/create_charge_order'
    DIZPAY_CREATE_PAYOUT_ORDER = 'https://api.dizpay.com/v2/member/orders/create_payout_order'
    DIZPAY_QUERY_ORDER = 'https://api.dizpay.com/v2/member/orders/query_order'
    DIZPAY_PAY_ORDER = 'https://api.dizpay.com/v2/member/orders/pay_order'
    DIZPAY_QUERY_CURRENCY = 'https://api.dizpay.com/v2/member/rates/currency'

    SQLALCHEMY_DATABASE_URL = 'mysql://icaicloud:9o4&^ZCLY05c@icaicloud-prod-cluster.cluster-c9650aehmgko.ap-southeast-1.rds.amazonaws.com:3306/icaisms-api-prod?charset=utf8mb4'

    TIMEZONE = 'Asia/Shanghai'

    KEY = 'carlzhuangzhao12'

    DIZPAY_QUERY_CURRENCY = 'https://api.dizpay.com/v2/member/rates/currency'

    EMAIL_FROM_ADDRESS = '财信<no-reply@cmessages.com>'

    EMAIL_API_URL = 'http://icaimail-api/mail/send'

    EMAIL_API_SECRET = 'n8bW3nymDzsYv0vsnKfCcGiGR'

    EMAIL_RESET_PASSWORD = "https://dashboard.cmessages.com/#/reset?email={email}&code={code}"
    EMAIL_RESET_PASSWORD_TITLE = "Reset your password"
    EMAIL_RESET_PASSWORD_TEMPLATE = 'cmessages-confirm-reset'

    EMAIL_ACTIVE_ACCOUNT = "https://dashboard.cmessages.com/#/login?email={email}&code={code}"
    EMAIL_ACTIVE_TEMPLATE = 'cmessages-confirm-email'
    EMAIL_ACTIVE_MAIL_TITLE = "Your Account is almost ready"

    EMAIL_PIN_CODE_MAIL_TITLE = 'Your CMessages Pin Code'
    EMAIL_PIN_CODE_MAIL_TEMPLATE = 'cmessages-code'