# -*- coding: utf-8 -*-
import decimal
import logging

from app.engine import StandardHandler, handler_list
from app.model.admin_user import AdminUser
from app.model.schedule_task import ScheduleTaskBase, UserRegisterScheduleTask
from app.model.sms_product import SmsChannel, SmsProduct
from app.model.sms_user import SmsUser
from app.model.user import User
from sqlalchemy.orm import Session
from app.model.setting import Setting


q = decimal.Decimal('1.000')

def round_price(d: decimal.Decimal):
    return d.quantize(q, decimal.ROUND_UP)


def expired_handler(task: UserRegisterScheduleTask, session: Session):
    # task.user.update_placement_left_right_id(session)
    # task.user.update_left_right_id(session)
    # session.flush()

    user: User = task.user
    logging.info("Process user register %s", user.id)
    products = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == user.admin_user_id).all()
    logging.info("Found root %d products", len(products))
    if len(products) == 0:
        return False

    setting = Setting.get_json(session, 'general_option')

    profit_rate_default = decimal.Decimal(
        setting['profit_rate_default']) / 100 + 1

    for item in products:
        sms_user = session.query(SmsUser).filter(
            SmsUser.user_id == user.id,
            SmsUser.country == item.country,
            SmsUser.type == item.type,
            SmsUser.channel_name == item.channel_name
        ).first()
        if sms_user is not None:
            logging.info("SmsUser exists. country=%s channel_name=%s type=%d",
                         item.country, item.channel_name, item.type)
            return
        sms_user = SmsUser(user_id=task.user_id,
                           channel_name=item.channel_name,
                           country=item.country,
                           country_code=item.country_code,
                           type=item.type,
                           provider=item.provider,
                           price=item.list_price,
                           default_price=item.list_price
                           )
        if item.cost_price >= item.list_price:
            sms_user.price = item.price * profit_rate_default
            sms_user.default_price = item.price * profit_rate_default

        logging.info("Create new SmsUser country=%s channel_name=%s type=%d price=%s",
                     item.country, item.channel_name, item.type, sms_user.price)
        session.add(sms_user)
        session.flush()
    return False


class UserRegisterHandler(StandardHandler):
    def __init__(self):
        super(UserRegisterHandler, self).__init__(UserRegisterScheduleTask)

    def get_schedule_task_handlers(self):
        return [expired_handler]


handler_list.append(UserRegisterHandler())
