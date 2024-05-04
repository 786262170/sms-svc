# -*- coding: utf-8 -*-
import hashlib
import datetime
import logging
import time
import requests
import urllib.parse

from sdk import SmsDriver, SmsError, SmsExceptionEnum, SmsStatus
from sdk.util import divide_chunks


class SkyLineSms(SmsDriver):

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.send_limit = 1000
        self.status_limit = 100

    @staticmethod
    def error_code(status):
        status_dict = {
            -1: SmsExceptionEnum.NOT_PERMISSION,
            -2: SmsExceptionEnum.IP_LIMIT,
            -3: SmsExceptionEnum.CONTENT_ERROR,
            -4: SmsExceptionEnum.CONTENT_IS_EMPTY,
            -5: SmsExceptionEnum.CONTENT_TOO_LARGE,
            -7: SmsExceptionEnum.PHONE_TOO_LARGE,
            -8: SmsExceptionEnum.PHONE_IS_EMPTY,
            -9: SmsExceptionEnum.PHONE_IS_ERROR,
            -10: SmsExceptionEnum.BALANCE_LACK,
            -13: SmsExceptionEnum.ACCOUNT_LOCK
        }
        if status in status_dict:
            return status_dict[status]
        else:
            return SmsExceptionEnum.SYSTEM_ERROR

    @staticmethod
    def exchange_status(status):
        status_dict = {
            0: SmsStatus.SUCCESS,
            1: SmsStatus.PENDING,
            2: SmsStatus.PROCESS,
        }
        if status in status_dict:
            return status_dict[status]
        else:
            return SmsStatus.FAIL

    def get_sign(self):
        now_str = time.strftime("%Y%m%d%H%M%S", time.localtime())
        signature_content = self.app_id + self.app_key + now_str
        signature_content = signature_content.encode('utf-8')
        signature = hashlib.md5(signature_content).hexdigest()
        return signature, now_str

    def send_sms(self, phone_list: list, content) -> list:
        signature, now_str = self.get_sign()
        if len(content) > 1024:
            raise SmsError(SmsExceptionEnum.CONTENT_TOO_LONG, '短信内容过长')
        data = {
            'numbers': ','.join(phone_list),
            'content': urllib.parse.quote(content)
        }
        params = {
            'account': self.app_id,
            'sign': signature,
            'datetime': now_str
        }
        r = requests.post(
            'http://sms.skylinelabs.cc:20003/sendsmsV2', json=data, params=params)
        logging.info("[skyline(%s)] send sms result: %s", self.app_id, r.text)
        result = r.json()
        if result['status'] == 0:
            return [{'phone': str(x[0]), 'id': str(x[1])} for x in result['array']]
        else:
            raise SmsError(SkyLineSms.error_code(result['status']), '发送失败')

    def get_status(self, ids: list):
        signature, now_str = self.get_sign()
        params = {
            'account': self.app_id,
            'sign': signature,
            'datetime': now_str,
            'ids': ','.join(ids)
        }
        r = requests.get(
            'http://sms.skylinelabs.cc:20003/getreportV2', params=params)

        result = r.json()
        if result['status'] == 0:

            result_list = [{'phone': x[1],
                            'id': str(x[0]),
                            # 'time': datetime.datetime.strptime(str(x[2]), '%Y%m%d%H%M%S'),
                            'status': SkyLineSms.exchange_status(x[3])} for x in result['array']]
            return result_list
        else:
            raise SmsError(SkyLineSms.error_code(result['status']), '查询失败')
