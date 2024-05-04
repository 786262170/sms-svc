# -*- coding: utf-8 -*-
import logging
import json
import time
import traceback
import datetime

from sqlalchemy.orm.session import Session
from app.model import SessionLocal
from app.model.message import MessageCheck, MessageStatus
from app.model.user import User, UserBalanceType, UserBalanceRecordType
from app.model.sms_product import SmsProduct, SmsProductProvider, SmsChannel, SmsSpecialCheck, SmsSpecialNotFoundRecord
from configuration import load_config
from sdk import SmsStatus


class Engine(object):
    @staticmethod
    def invalid_check(session, name):
        q = session.query(MessageCheck).filter(MessageCheck.sms_product_id == SmsProduct.id,
                                               SmsProduct.channel_name == name,
                                               MessageCheck.message_number.is_(None),
                                               MessageCheck.status == MessageStatus.PENDING.value).limit(500).all()
        if len(q) == 0:
            return False

        for item in q:
            message_check: MessageCheck = session.query(MessageCheck).get(item.id)
            message_check.status = MessageStatus.FINISH.value
            message_check.processed_at = datetime.datetime.now()
            message_check.message_status = SmsStatus.FAIL.value
            message_check.price = 0
            user = session.query(User).get(message_check.user_id)

            user.update_balance(session, UserBalanceType.FROZEN, - message_check.price, UserBalanceRecordType.REFUND)
            session.commit()

        return True

    @staticmethod
    def confirm_all(session: Session, name: str) -> bool:
        message_check_list: list[MessageCheck] = session.query(MessageCheck).filter(
            MessageCheck.sms_product_id == SmsProduct.id,
            SmsProduct.channel_name == name,
            MessageCheck.status == MessageStatus.PENDING.value).limit(1000).all()
        if len(message_check_list) == 0:
            return False
        for message_check in message_check_list:
            message_check.status = MessageStatus.FINISH.value
            message_check.processed_at = datetime.datetime.now()
            message_check.message_status = SmsStatus.SUCCESS.value

            user = session.query(User).get(message_check.user_id)

            user.update_balance(session, UserBalanceType.BASE, -message_check.price, UserBalanceRecordType.CONSUME,
                                {'message': '短信扣费'})
            user.update_balance(session, UserBalanceType.FROZEN, -message_check.price, UserBalanceRecordType.CONSUME,
                                {'message': '短信扣费'})
            user.admin_user.update_profit(message_check)
        session.commit()
        return True

    @staticmethod
    def run():
        while True:
            change_flag = False
            session = SessionLocal()
            try:
                channel_list = session.query(SmsChannel).filter(
                    SmsChannel.provider == SmsProductProvider.CMCOM.value).all()

                for channel in channel_list:
                    change_flag |= Engine.invalid_check(session, channel.name)
                    change_flag |= Engine.confirm_all(session, channel.name)

            except Exception as e:
                logging.error(traceback.format_exc())
                session.rollback()
                logging.error('Engine.run error exception: {}'.format(e))
                time.sleep(20)

            session.close()
            if not change_flag:
                time.sleep(1)


if __name__ == '__main__':
    config = load_config()
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='[%Y-%m-%d %H:%M:%S]')
    Engine.run()
