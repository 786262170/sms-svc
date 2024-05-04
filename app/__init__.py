# -*- coding: utf-8 -*-
import logging

from fastapi import FastAPI

from configuration import load_config


def create_api():
    config = load_config()
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='[%Y-%m-%d %H:%M:%S]')

    app = FastAPI(debug=config.DEBUG,
                  title=config.PRODUCT_NAME)

    from app.api import pin_code
    app.include_router(pin_code.router, prefix="/pin_code", tags=['验证码'])

    from app.api.member import user
    app.include_router(user.router, prefix="/member/user", tags=['会员端 用户'])

    from app.api.member import application
    app.include_router(application.router, prefix="/member/application", tags=['会员端 应用'])

    from app.api.member import contact
    app.include_router(contact.router, prefix="/member/contact", tags=['会员端 联系人'])

    from app.api.member import wallet
    app.include_router(wallet.router, prefix="/member/wallet", tags=['会员端 钱包'])

    from app.api.member import wallet_order
    app.include_router(wallet_order.router, prefix="/member/wallet_order", tags=['会员端 钱包订单'])

    from app.api.member import message_template
    app.include_router(message_template.router, prefix="/member/message_template", tags=['会员端 消息模板'])

    from app.api.member import message
    app.include_router(message.router, prefix="/member/message", tags=['会员端 消息'])

    from app.api.member import product
    app.include_router(product.router, prefix="/member/product", tags=['会员端 产品'])

    from app.api.member import setting
    app.include_router(setting.router, prefix="/member/setting", tags=['会员端 设置'])

    from app.api.member import currency
    app.include_router(currency.router, prefix="/member/currency", tags=['会员端 法币'])

    from app.api.admin import user
    app.include_router(user.router, prefix="/admin/user", tags=['管理端 用户'])

    from app.api.admin import application
    app.include_router(application.router, prefix="/admin/application", tags=['管理端 应用'])

    from app.api.admin import contact
    app.include_router(contact.router, prefix="/admin/contact", tags=['管理端 联系人'])

    from app.api.admin import member
    app.include_router(member.router, prefix="/admin/member", tags=['管理端 会员'])

    from app.api.admin import profit
    app.include_router(profit.router, prefix="/admin/profit", tags=['管理端 收益'])

    from app.api.admin import wallet
    app.include_router(wallet.router, prefix="/admin/wallet", tags=['管理端 会员钱包'])

    from app.api.admin import wallet_order
    app.include_router(wallet_order.router, prefix="/admin/wallet_order", tags=['管理端 会员钱包订单'])

    from app.api.admin import message_template
    app.include_router(message_template.router, prefix="/admin/message_template", tags=['管理端 消息模板'])

    from app.api.admin import member_product
    app.include_router(member_product.router, prefix="/admin/member_product", tags=['管理端 会员产品'])

    from app.api.admin import product
    app.include_router(product.router, prefix="/admin/product", tags=['管理端 产品'])

    from app.api.admin import setting
    app.include_router(setting.router, prefix="/admin/setting", tags=['管理端 设置'])

    from app.api.sms import api
    app.include_router(api.router, prefix="/sms", tags=['HTTP API接口'])

    if config.DEBUG_API:
        from app.api.debug import debug
        app.include_router(debug.router, prefix="/debug", tags=['调试接口'])

    return app
