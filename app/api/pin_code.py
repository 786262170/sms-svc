# -*- coding: utf-8 -*-
from app.utils.email import send_mail_with_template
import random
import uuid
from io import BytesIO

from captcha.image import ImageCaptcha
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sendgrid import Mail, SendGridAPIClient
from sqlalchemy.orm import Session
from starlette.responses import Response
from yunpian_python_sdk.model import constant as YC
from yunpian_python_sdk.model.constant import YP_SMS_HOST
from yunpian_python_sdk.ypclient import YunpianClient

from app.api import get_db, BsException, BsExceptionEnum, app_config
from app.model.pin_code import CaptchaPinCode, SmsPinCode, EmailPinCode

router = APIRouter()


@router.get("/captcha")
def captcha_pin_code(uuid: str = str(uuid.uuid4()),
                     session: Session = Depends(get_db)):
    chars = "abcdedfhkmnpqrtuvwxy2346789ABCDEFGHKLMNPQRTUVWXY2346789"
    code = ''.join(random.sample(chars, 4)).lower()
    image = ImageCaptcha()
    data = image.generate_image(code)
    out = BytesIO()
    data.save(out, "jpeg", quality=75)

    pin_code = session.query(CaptchaPinCode).get(uuid)
    if pin_code is None:
        pin_code = CaptchaPinCode(id=uuid)
    code = code.lower()
    pin_code.generate_signature(session, code)

    return Response(out.getvalue(), media_type="image/png")


class SMSPinCodeRequest(BaseModel):
    mobile: str = Field(..., min_length=8, max_length=15)
    sms_template: str = Field('【DIZ】 Your verification code is {code}', description='短信模板内容')


@router.post('/sms')
def sms_pin_code(data: SMSPinCodeRequest,
                 session: Session = Depends(get_db)):
    code = str(random.randint(100000, 999999))
    mobile = data.mobile
    if '+' not in mobile:
        mobile = "+" + mobile
    clnt = YunpianClient('92a91a6d83c70bd2a4d7bce9033bc0f2', {YP_SMS_HOST: "https://us.yunpian.com"})
    param = {YC.MOBILE: mobile, YC.TEXT: data.sms_template.format(code=code)}
    r = clnt.sms().single_send(param)
    if r.code() != 0:
        raise BsException(BsExceptionEnum.SEND_SMS_ERROR, {'msg': r.msg()})

    pin_code = session.query(SmsPinCode).get(data.mobile)
    if pin_code is None:
        pin_code = SmsPinCode(id=data.mobile)
    pin_code.generate_signature(session, code)

    return {}


class EmailPinCodeRequest(BaseModel):
    email: EmailStr
    # template_id: str


# 邮箱验证码
@router.post('/email_pin_code')
def email_pin_code(data: EmailPinCodeRequest,
                   session: Session = Depends(get_db)):
    code = str(random.randint(100000, 999999))

    pin_code = session.query(EmailPinCode).get(data.email)
    if pin_code is None:
        pin_code = EmailPinCode(id=data.email)
    expires_minutes = 30
    pin_code.generate_signature(session, code, expires_minutes * 60)  # 有效期 30 分钟
    send_mail_with_template(data.email,
        app_config.EMAIL_PIN_CODE_MAIL_TITLE,
        app_config.EMAIL_PIN_CODE_MAIL_TEMPLATE,
        {
            'code': code,
            'expiresMinutes': expires_minutes 
        })
