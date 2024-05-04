# -*- coding: utf-8 -*-
import logging
import json
import time
import traceback
import datetime

from sqlalchemy import literal
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import false
from app.model import SessionLocal
from app.model.message import MessageCheck, MessageStatus
from app.model.user import User, UserBalanceType, UserBalanceRecordType
from app.model.sms_product import SmsProduct, SmsProductProvider, SmsChannel, SmsSpecialCheck, SmsSpecialNotFoundRecord
from configuration import load_config
from sdk import SmsStatus
from sdk.nxcloud import NXCloudSms


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

            user.update_balance(session, UserBalanceType.FROZEN, -
                                message_check.price, UserBalanceRecordType.REFUND)
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

            user.update_balance(session, UserBalanceType.BASE, -message_check.price,
                                UserBalanceRecordType.CONSUME, {'message': '短信扣费'})
            user.update_balance(session, UserBalanceType.FROZEN, -message_check.price,
                                UserBalanceRecordType.CONSUME, {'message': '短信扣费'})
            user.admin_user.update_profit(message_check)
        session.commit()
        return True

    @staticmethod
    def nx_status_get(session, name, app_id, app_key):

        sms_special_check = session.query(SmsSpecialCheck).filter(
            SmsSpecialCheck.channel_name == name).first()

        if sms_special_check is None:
            return False

        nx_api = NXCloudSms(app_id, app_key)

        result = nx_api.get_status(sms_special_check.date.strftime('%Y%m%d'), sms_special_check.page_size,
                                   int(sms_special_check.num / sms_special_check.page_size) + 1)
        if result['total'] == 0 or (sms_special_check.num != 0 and result['total'] <= sms_special_check.num):
            now = datetime.datetime.now()
            if sms_special_check.date + datetime.timedelta(days=1, minutes=5) < now:
                sms_special_check.date = sms_special_check.date + \
                    datetime.timedelta(days=1)
                sms_special_check.num = 0
                session.commit()
            return False

        pos = int(sms_special_check.num % sms_special_check.page_size)
        result_list = \
            [{'phone': item['phone'], 'id': item['msgid'], 'status': item['dr']}
                for item in result['rows'][pos:]]

        if len(result_list) == 0:
            return False

        for result_item in result_list:
            sms_special_check.num += 1

            # 对比每一条进行更新message_number和状态并且扣费和发放奖金，更新 SmsSpecialCheck
            message_check: MessageCheck = session.query(MessageCheck).filter(
                MessageCheck.phone_number == result_item['phone'],
                literal(result_item['id']).contains(
                    MessageCheck.message_number),
                MessageCheck.status == MessageStatus.PENDING.value).first()

            if message_check is None:
                record = session.query(SmsSpecialNotFoundRecord).filter(
                    SmsSpecialNotFoundRecord.channel_name == sms_special_check.channel_name,
                    SmsSpecialNotFoundRecord.num == sms_special_check.num,
                    SmsSpecialNotFoundRecord.date == sms_special_check.date).first()
                if record is not None:
                    continue

                record = SmsSpecialNotFoundRecord(channel_name=sms_special_check.channel_name,
                                                  num=sms_special_check.num,
                                                  date=sms_special_check.date,
                                                  info=json.dumps(result_item))
                session.add(record)
                session.flush()
                continue

            message_check.status = MessageStatus.FINISH.value
            message_check.processed_at = datetime.datetime.now()
            message_check.message_number = result_item['id']

            if result_item['status'] == 'DELIVRD':
                message_check.message_status = SmsStatus.SUCCESS.value
                user = session.query(User).get(message_check.user_id)

                user.update_balance(session, UserBalanceType.BASE, -message_check.price,
                                    UserBalanceRecordType.CONSUME, {'message': '短信扣费'})
                user.update_balance(session, UserBalanceType.FROZEN, -message_check.price,
                                    UserBalanceRecordType.CONSUME, {'message': '短信扣费'})

                user.admin_user.update_profit(message_check)

            else:  # UNDELIV
                message_check.message_status = SmsStatus.FAIL.value
                message_check.price = 0
                user = session.query(User).get(message_check.user_id)

                user.update_balance(session, UserBalanceType.FROZEN, -message_check.price,
                                    UserBalanceRecordType.REFUND)

            session.commit()

        return True

    @staticmethod
    def run():
        while True:
            change_flag = False
            session = SessionLocal()
            try:
                channel_list = session.query(SmsChannel).filter(
                    SmsChannel.provider == SmsProductProvider.NX.value).all()

                for channel in channel_list:
                    change_flag |= Engine.invalid_check(session, channel.name)
                    change_flag |= Engine.confirm_all(session, channel.name)
                    # change_flag |= Engine.nx_status_get(
                    #     session, channel.name, channel.app_id, channel.app_key)

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
