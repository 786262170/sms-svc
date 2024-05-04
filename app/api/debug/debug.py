# -*- coding: utf-8 -*-
import time
import urllib

import phonenumbers

from app.api import BsException, BsExceptionEnum, GetSession
from app.model.admin_user import AdminUser
from app.model.sms_product import SmsChannel
from app.model.user import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response

from sdk.cmcom import CmcomSms
from sdk.sms_api import SmsApi

router = APIRouter()


@router.get('/token/admin')
def get_admin_user_token(
        uid: str,
        response: Response,
        session: Session = Depends(GetSession())):
    admin_user = session.query(AdminUser).filter(AdminUser.uid == uid).first()
    if admin_user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')
    admin_user.generate_auth_token()
    response.set_cookie(key='token', value=str(
        admin_user.token, encoding='utf-8'), max_age=(60 * 60 * 24 * 365))
    session.commit()
    return {
        'token': admin_user.token
    }


@router.get('/token/user')
def get_admin_user_token(
        uid: str,
        response: Response,
        session: Session = Depends(GetSession())):
    admin_user = session.query(User).filter(User.uid == uid).first()
    if admin_user is None:
        raise BsException(BsExceptionEnum.USER_NOT_EXIST, 'user not exist')
    admin_user.generate_auth_token()
    response.set_cookie(key='token', value=str(
        admin_user.token, encoding='utf-8'), max_age=(60 * 60 * 24 * 365))
    session.commit()
    return {
        'token': admin_user.token
    }


@router.get('/my/test')
def my_test_cmtelecom():
    # sms发送接口
    # rt = CmcomSms('', '07da6932-ee90-475a-8802-f42d2dfef2c8').send_sms(['8615057234281','8615057234282'], 'The audience 9 folded up！oop 182')

    # sms_api = SmsApi(2, 'dizpay', '07da6932-ee90-475a-8802-f42d2dfef2c8')
    # rt = sms_api.send_sms(['14693892766'], '07da6932-ee90-475a-8802-f42d2dfef2c8 老美号测试')

    # sms_api = SmsApi(2, 'dizpay', '07da6932-ee90-475a-8802-f42d2dfef2c8')
    # rt = sms_api.send_sms(['14405572072'], '07da6932-ee90-475a-8802-f42d2dfef2c8 本地美国号xxx测试')

    sms_api = SmsApi(2, 'dizpay', 'dad5b394-5dfb-4e60-ab5b-e3dcf3bd093a')
    rt = sms_api.send_sms(['4693892766'], 'dad5b394-5dfb-4e60-ab5b-e3dcf3bd093a test cm message.')
    # rt = sms_api.send_sms_chunked(['8615057234281','sdsdsd'], 'dad5b394-5dfb-4e60-ab5b-e3dcf3bd093a 899')

    # sms_api = SmsApi(2, 'dizpay', 'e366267b-e824-43a0-923c-2319c49196ad')
    # rt = sms_api.send_sms(['8615057234281'], 'e366267b-e824-43a0-923c-2319c49196ad 899')

    return {
        'token': "xxx",
        'rt': rt
    }


@router.get('/my/smsconf')
def my_sms_conf(session: Session = Depends(GetSession())):
    # rt = session.query(SmsChannel).all()
    # mobile = '14405572072'
    # mobile = '+{}'.format(mobile)
    # number = phonenumbers.parse(mobile)
    # country = phonenumbers.region_code_for_number(number)  # 可获取国家名称
    # country_code = number.country_code
    # mobile = number.national_number
    #
    # phone_number = '{}{}'.format(country_code, mobile)

    # cursor = session.execute('select * from sms_user limit 10')
    # result = cursor.fetchall()
    #
    # session.execute('SET FOREIGN_KEY_CHECKS =(:value)', params={"value": 0})
    # session.commit()
    #
    # session.query(SmsChannel).filter(SmsChannel.name =='skyline_02_z').update({SmsChannel.name: 'skyline_02'})
    #
    # session.execute('SET FOREIGN_KEY_CHECKS =(:value)', params={"value": 1})
    # session.commit()

    return {
        # 'rt': rt,
        # 'result': result,
        # 'country': country,
        # 'phone_number': phone_number,
    }
