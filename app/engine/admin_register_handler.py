# -*- coding: utf-8 -*-
import decimal
from app.engine import handler_list, StandardHandler
from app.model.schedule_task import AdminRegisterScheduleTask
from app.model.sms_product import SmsProduct
from app.model.setting import Setting


q = decimal.Decimal('1.000')


def round_cost_price(d: decimal.Decimal):
    return d.quantize(q, decimal.ROUND_DOWN)


def round_price(d: decimal.Decimal):
    return d.quantize(q, decimal.ROUND_UP)


def expired_handler(task, session):
    # task.user.update_placement_left_right_id(session)
    # task.user.update_left_right_id(session)
    # session.flush()

    if task.admin_user.parent_id is None:
        return False

    product = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == task.admin_user_id).first()
    if product is not None:
        return False

    setting = Setting.get_json(session, 'general_option')

    profit_rate_default = decimal.Decimal(
        setting['profit_rate_default']) / 100 + 1

    q = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == task.admin_user.parent_id).all()
    for item in q:
        product = session.query(SmsProduct).filter(
            SmsProduct.admin_user_id == task.admin_user_id,
            SmsProduct.country == item.country,
            SmsProduct.channel_name == item.channel_name).first()
        if product is not None:
            return
        product = SmsProduct(admin_user_id=task.admin_user_id,
                             channel_name=item.channel_name,
                             country=item.country,
                             country_code=item.country_code,
                             type=item.type,
                             provider=item.provider,
                             price=round_price(
                                 item.price * profit_rate_default),
                             cost_price=round_cost_price(item.price),
                             list_price=round_cost_price(item.list_price),
                             channel_price=round_cost_price(item.channel_price)
                             )
        if product.cost_price >= product.list_price:
            product.list_price = round_cost_price(product.cost_price * profit_rate_default)

        session.add(product)
        session.flush()

    return False


class AdminRegisterHandler(StandardHandler):
    def __init__(self):
        super(AdminRegisterHandler, self).__init__(AdminRegisterScheduleTask)

    def get_schedule_task_handlers(self):
        return [expired_handler]


handler_list.append(AdminRegisterHandler())
