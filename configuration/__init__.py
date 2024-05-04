# -*- coding: utf-8 -*-
import os


def load_config():
    mode = os.environ.get('MODE')
    if mode == 'production':
        from configuration.production import ProductionConfig
        return ProductionConfig
    elif mode == 'staging':
        from configuration.staging import StagingConfig
        return StagingConfig
    else:
        from configuration.development import DevelopmentConfig
        return DevelopmentConfig
