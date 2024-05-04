# -*- coding: utf-8 -*-
from configuration.development import DevelopmentConfig


class StagingConfig(DevelopmentConfig):
    DEBUG = False
    DEBUG_API = True

    LOG_LEVEL = 'DEBUG'

    PRODUCT_NAME = 'icaisms-api-staging'

    # SQLALCHEMY_DATABASE_URL = 'mysql://root:zCLZpdZD3DrwqG2!@134.175.97.227:3306/icaisms?charset=utf8mb4'
    SQLALCHEMY_DATABASE_URL = 'mysql://icaicloud:9o4&^ZCLY05c@icaicloud-prod-cluster.cluster-c9650aehmgko.ap-southeast-1.rds.amazonaws.com:3306/icaisms-api?charset=utf8mb4'

    SQLALCHEMY_ECHO = False
