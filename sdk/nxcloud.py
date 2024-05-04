# -*- coding: utf-8 -*-
import logging
import requests
import urllib.parse

from sdk import SmsDriver, SmsExceptionEnum, SmsError


class NXCloudSms(SmsDriver):

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        self.send_limit = 1000
        self.status_limit = 100

    @staticmethod
    def error_code(status):
        status_dict = {
            '1': SmsExceptionEnum.NOT_PERMISSION,
            '9': SmsExceptionEnum.IP_LIMIT,
            '4': SmsExceptionEnum.CONTENT_ERROR,
            '5': SmsExceptionEnum.CONTENT_TOO_LARGE,
            '7': SmsExceptionEnum.PHONE_TOO_LARGE,
            '6': SmsExceptionEnum.PHONE_IS_ERROR,
            '3': SmsExceptionEnum.BALANCE_LACK,
        }
        if status in status_dict:
            return status_dict[status]
        else:
            return SmsExceptionEnum.SYSTEM_ERROR

    def send_sms(self, phone_list: list, content) -> list:
        data = {
            'appkey': self.app_id,
            'secretkey': self.app_key,
            'phone': ','.join(phone_list),
            'content': urllib.parse.quote(content)
        }
        r = requests.post('http://api2.nxcloud.com/api/sms/mtsend', data=data)
        logging.info("[nxcloud %s] send sms result: %s", self.app_id, r.text) 
        result = r.json()
        result_list = []
        if result['code'] == '0':
            for phone in phone_list:
                result_list.append({'phone': phone, 'id': result['messageid']})
            return result_list
        else:
            raise SmsError(NXCloudSms.error_code(result['code']), '发送失败')

    def get_status(self, date: str, page_size: int, page: int):
        """
        :param date: yyyyMMdd
        :param page_size: < 1000
        :param page:
        :return:{
                "total": 13,
                "pageSize": 1,
                "page": 1,
                "rows": [
                    {
                        "billing_size": 1,
                        "date": "2021-07-22 22:37:00",
                        "senderid": "",
                        "phone": "16014635797",
                        "dr_time": "2021-07-22 22:37:01",
                        "billing_price": 0.018,
                        "msgid": "20210722223600592-9359029269",
                        "billing_status": "是",
                        "body": "testq",
                        "dr_status": "成功",
                        "dr": "DELIVRD",
                        "network": "AT&T MOBILITY"
                    }
                ]}
        """
        data = {
            'appkey': self.app_id,
            'secretkey': self.app_key,
            'date': date,
            'page_size': page_size,
            'page': page
        }
        r = requests.post('http://api2.nxcloud.com/api/sms/getSmsCdr', data=data)
        result = r.json()
        if result['code'] == '0':
            return result['info']
        else:
            raise SmsError(NXCloudSms.error_code(result['code']), '发送失败')

    def get_one_status(self, date: str, messageid: str):
        """
        :param date: yyyyMMdd
        :param page_size: < 1000
        :param page:
        :return:{
                "code": "0",
                "row": {
                    "billing_size": 1,
                    "date": "2021-06-28 09:00:00",
                    "senderid": "666",
                    "phone": "6288888888888",
                    "dr_time": "2021-06-28 09:00:00",
                    "billing_price": 0.0,
                    "msgid": "xxxxxxxxxxxxxxxxxxxxxxxx",
                    "billing_status": "否",
                    "body": "hello, your code is 888888",
                    "dr_status": "成功",
                    "dr": "DELIVRD",
                    "network": "PT TELEKOMUNIKASI SELULAR"
                }
                }
        """
        data = {
            'appkey': self.app_id,
            'secretkey': self.app_key,
            'date': date,
            'messageid': messageid
        }
        r = requests.post('http://api2.nxcloud.com/api/sms/get', data=data)
        result = r.json()
        if result['code'] == '0':
            return result['row']
        else:
            raise SmsError(NXCloudSms.error_code(result['code']), '发送失败')
