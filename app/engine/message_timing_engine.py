# -*- coding: utf-8 -*-
import logging
import json
import time
import traceback
import datetime
import phonenumbers

from app.model import SessionLocal
from app.model.message import MessageTiming, MessageStatus, MessageCheck, MessageTimingFrequency, \
    MessageType
from app.model.user import User
from app.model.contact import Contact
from app.model.sms_product import SmsProductType
from configuration import load_config
from app.model.sms_user import SmsUser
from sdk.sms_api import SmsApi


class Engine(object):
    @staticmethod
    def send_message(session, message_timing: MessageTiming):

        mobile_list = json.loads(message_timing.mobile)
        country_phone_dict = {}
        filtered_mobile = []
        for item in mobile_list:
            mobile = item

            try:
                mobile = '+{}'.format(mobile)
                number = phonenumbers.parse(mobile)
                country = phonenumbers.region_code_for_number(number)  # 可获取国家名称
                country_code = number.country_code
                mobile = number.national_number

                phone_number = '{}{}'.format(country_code, mobile)
            except Exception as e:
                filtered_mobile.append(item)
                logging.error('send_message phonenumbers error exception: {}'.format(e))
                continue

            if country_phone_dict.get(country) is None:
                country_phone_dict.update({country: [phone_number]})
            else:
                country_phone_dict[country].append(phone_number)

        current_user = message_timing.user

        # 查找最适合的sms产品
        country_list = [country for country in country_phone_dict]
        price_product_dict = SmsUser.country_get_price_product(session, current_user, country_list,
                                                               SmsProductType.MESSAGING, None)

        amount = 0
        for country in country_phone_dict:
            phone_list = country_phone_dict[country]
            if country not in price_product_dict:
                filtered_mobile.extend(phone_list)
                continue
            amount += price_product_dict[country]['price'] * len(phone_list)

        # 判断冻结的金额是否大于余额，是的话不允许发送
        ret = session.query(User).filter(User.id == current_user.id,
                                         User.balance > User.frozen_balance + amount).update(
            dict(frozen_balance=User.frozen_balance + amount))
        if ret != 1:
            return

        for country in country_phone_dict:
            if country not in price_product_dict:
                continue
            phone_list = country_phone_dict[country]
            price = price_product_dict[country]['price']
            sms_product = price_product_dict[country]['product']

            # sms发送接口
            sms_api = SmsApi(sms_product.provider, sms_product.channel.app_id, sms_product.channel.app_key)

            content = message_timing.content
            try:
                result_list = sms_api.send_sms(phone_list, content)
                message_timing.delivered_count += len(phone_list)
            except Exception as e:
                logging.error('send_message send_sms error exception: {}'.format(e))
                result_list = []
                for phone in phone_list:
                    result_list.append({'phone': phone, 'id': None})

            for result_dict in result_list:
                # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
                message_check = MessageCheck(user_id=current_user.id,
                                             message_timing_id=message_timing.id,
                                             country=sms_product.country,
                                             sms_product_id=sms_product.id,
                                             phone_number=result_dict['phone'],
                                             message_number=result_dict['id'],
                                             content=content,
                                             price=price)
                session.add(message_check)
        message_timing.filtered_mobile = json.dumps(filtered_mobile)
        message_timing.filtered_mobile_count = len(filtered_mobile)
        return

    @staticmethod
    def group_send_message(session, message_timing:MessageTiming):

        contact_list = session.query(Contact).filter(Contact.user_id == message_timing.user_id,
                                                     Contact.group_id == message_timing.group_id).all()
        if contact_list is None or len(contact_list) == 0:
            return
        filtered_mobile = []
        for contact in contact_list:
            mobile = contact.mobile
            content = message_timing.content.format(first_name=contact.first_name,
                                                    last_name=contact.last_name,
                                                    title=contact.title,
                                                    company=contact.company)

            try:
                mobile, price, product = SmsUser.phone_get_price_product(
                    session, message_timing.user, mobile, SmsProductType.MESSAGING, None)
            except Exception as e:
                filtered_mobile.append(mobile)
                logging.error('group_send_message phone_get_price_product error exception: {}'.format(e))
                continue

            # 判断冻结的金额是否大于余额，是的话不允许发送
            ret = session.query(User).filter(User.id == message_timing.user_id,
                                             User.balance >= User.frozen_balance + price).update(
                dict(frozen_balance=User.frozen_balance + price))
            if ret != 1:
                continue

            # sms发送接口
            sms_api = SmsApi(product.provider, product.channel.app_id, product.channel.app_key)
            phone_list = [mobile]
            try:
                result_list = sms_api.send_sms(phone_list, content)
                message_timing.delivered_count += len(phone_list)
            except Exception as e:
                filtered_mobile.append(mobile)
                logging.error('group_send_message send_sms error exception: {}'.format(e))
                continue

            # 发送接口返回后，将所有的phone number和message number记录下来，即创建MessageCheck
            message_check = MessageCheck(user_id=message_timing.user_id,
                                         message_timing_id=message_timing.id,
                                         country=product.country,
                                         sms_product_id=product.id,
                                         phone_number=result_list[0]['phone'],
                                         message_number=result_list[0]['id'],
                                         content=content,
                                         price=price)
            session.add(message_check)
        message_timing.filtered_mobile = json.dumps(filtered_mobile)
        message_timing.filtered_mobile_count = len(filtered_mobile)
        return

    @staticmethod
    def run():
        while True:
            change_flag = False
            session = SessionLocal()
            try:
                now = datetime.datetime.now()
                message_timing = session.query(MessageTiming).filter(
                    MessageTiming.timing_at <= now,
                    MessageTiming.status == MessageStatus.PENDING.value,
                    MessageTiming.invalid == 0).first()

                if message_timing is not None:
                    if message_timing.type == MessageType.NORMAL.value or message_timing.group_id is None:
                        Engine.send_message(session, message_timing)
                    else:
                        Engine.group_send_message(session, message_timing)
                    message_timing.processed_at = datetime.datetime.now()
                    message_timing.status = MessageStatus.FINISH.value

                    if message_timing.frequency == MessageTimingFrequency.EVERY_DAY.value:
                        message_timing.status = MessageStatus.PENDING.value
                        timing_at = message_timing.timing_at
                        message_timing.timing_at = datetime.datetime(now.year, now.month, now.day, timing_at.hour,
                                                                     timing_at.minute,
                                                                     timing_at.second) + datetime.timedelta(days=1)

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
