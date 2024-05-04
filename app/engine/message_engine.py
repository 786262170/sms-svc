# -*- coding: utf-8 -*-
import logging
import json
import time
import traceback
import datetime
import phonenumbers

from app.model import SessionLocal
from app.model.message import Message, MessageType, MessageStatus, MessageCheck
from app.model.user import User
from app.model.contact import Contact
from app.model.sms_product import SmsProductType
from configuration import load_config
from app.model.sms_user import SmsUser
from sdk.sms_api import SmsApi


class Engine(object):
    @staticmethod
    def group_send_message(session, message):

        contact_list = session.query(Contact).filter(Contact.user_id == message.user_id,
                                                     Contact.group_id == message.group_id).all()
        if contact_list is None or len(contact_list) == 0:
            return

        for contact in contact_list:
            mobile = contact.mobile
            content = message.content.format(first_name=contact.first_name,
                                             last_name=contact.last_name,
                                             title=contact.title,
                                             company=contact.company)

            try:
                mobile, price, product = SmsUser.phone_get_price_product(
                    session, message.user, mobile, SmsProductType.MESSAGING, None)
            except Exception as e:
                logging.error('group_send_message phone_get_price_product error exception: {}'.format(e))
                continue

            # 判断冻结的金额是否大于余额，是的话不允许发送
            ret = session.query(User).filter(User.id == message.user_id,
                                             User.balance > User.frozen_balance + price).update(
                dict(frozen_balance=User.frozen_balance + price))
            if ret != 1:
                continue

            # sms发送接口
            sms_api = SmsApi(product.provider, product.channel.app_id, product.channel.app_key)
            phone_list = [mobile]
            try:
                result_list = sms_api.send_sms_chunked(phone_list, content)
            except Exception as e:
                logging.error('group_send_message send_sms error exception: {}'.format(e))
                result_list = []
                for phone in phone_list:
                    result_list.append({'phone': phone, 'id': None})

            # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
            message_check = MessageCheck(user_id=message.user_id,
                                         message_id=message.id,
                                         country=product.country,
                                         sms_product_id=product.id,
                                         phone_number=result_list[0]['phone'],
                                         message_number=result_list[0]['id'],
                                         content=content,
                                         price=price)
            session.add(message_check)
            session.commit()

        return

    @staticmethod
    def run():
        while True:
            change_flag = False
            session = SessionLocal()
            try:
                message = session.query(Message).filter(Message.status == MessageStatus.PENDING.value).first()

                if message is not None and message.group_id is not None:
                    Engine.group_send_message(session, message)
                    message.processed_at = datetime.datetime.now()
                    message.status = MessageStatus.FINISH.value
                    session.commit()

                    change_flag = True

            except Exception as e:
                logging.error(traceback.format_exc())
                session.rollback()
                logging.error('Engine.run error exception: {}'.format(e))
                time.sleep(1)

            session.close()
            if not change_flag:
                time.sleep(1)


if __name__ == '__main__':
    config = load_config()
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='[%Y-%m-%d %H:%M:%S]')
    Engine.run()
