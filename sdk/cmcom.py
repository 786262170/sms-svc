# -*- coding: utf-8 -*-
import json
import logging
import time
import uuid

import requests

from sdk import SmsDriver, SmsExceptionEnum, SmsError


class CmcomSms(SmsDriver):

    def __init__(self, app_id, app_key):
        # TODO 使用token
        self.app_id = app_id  # 此字段无用
        self.app_key = app_key  # apikey
        self.send_limit = 1000
        self.status_limit = 100

    @staticmethod
    def error_code(status):
        status_dict = {
            '101': SmsExceptionEnum.NOT_PERMISSION,
            '102': SmsExceptionEnum.BALANCE_LACK,
            '103': SmsExceptionEnum.NOT_PERMISSION,
            '201': SmsExceptionEnum.CONTENT_TOO_LARGE,
            '202': SmsExceptionEnum.CONTENT_MALFORMED,
            '203': SmsExceptionEnum.CONTENT_MALFORMED,
            '301': SmsExceptionEnum.CONTENT_MALFORMED,
            '302': SmsExceptionEnum.CONTENT_MALFORMED,
            '303': SmsExceptionEnum.PHONE_IS_ERROR,
            '304': SmsExceptionEnum.CONTENT_MALFORMED,
            '305': SmsExceptionEnum.CONTENT_MALFORMED,
            '401': SmsExceptionEnum.CONTENT_ERROR,
            '402': SmsExceptionEnum.PHONE_IS_ERROR,
            '403': SmsExceptionEnum.PHONE_IS_ERROR,
            '500': SmsExceptionEnum.SYSTEM_ERROR,
            '999': SmsExceptionEnum.SYSTEM_ERROR,
        }
        if status in status_dict:
            return status_dict[status]
        else:
            return SmsExceptionEnum.SYSTEM_ERROR

    def send_sms(self, phone_list: list, content) -> list:
        messages = [Message(content, 'AUTO', 'icaisms', phone_list)]
        data = self.encodeData(messages)

        # return data
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(data)),
        }
        r = requests.post('https://gw-cn.cmtelecom.com/v1.0/message', data=data, headers=headers)
        logging.info("[cmcom %s] send sms result: %s", self.app_key, r.text)
        result = r.json()
        if result['errorCode'] == 0:
            return [{'phone': str(x), 'id': str(result['messages'][0]['reference'])} for x in phone_list]
        else:
            raise SmsError(CmcomSms.error_code(result['errorCode']), '发送失败')

    def get_status(self, date: str, page_size: int, page: int):
        # TODO
        """

        """
        # data = {
        #     'appkey': self.app_id,
        #     'secretkey': self.app_key,
        #     'date': date,
        #     'page_size': page_size,
        #     'page': page
        # }
        # r = requests.post('http://api2.nxcloud.com/api/sms/getSmsCdr', data=data)
        # result = r.json()
        # if result['code'] == '0':
        #     return result['info']
        # else:
        #     raise SmsError(CmtelecomSms.error_code(result['code']), '发送失败')
        raise SmsError(CmcomSms.error_code(1), '发送失败')

    def get_one_status(self, date: str, messageid: str):
        # TODO
        """

        """
        # data = {
        #     'appkey': self.app_id,
        #     'secretkey': self.app_key,
        #     'date': date,
        #     'messageid': messageid
        # }
        # r = requests.post('http://api2.nxcloud.com/api/sms/get', data=data)
        # result = r.json()
        # if result['code'] == '0':
        #     return result['row']
        # else:
        #     raise SmsError(CmtelecomSms.error_code(result['code']), '发送失败')
        raise SmsError(CmcomSms.error_code(1), '发送失败')

        # Method to encode Data, Gateway accepts this format

    def encodeData(self, messages):
        # Set productToken
        data = {"messages": {"authentication": {"producttoken": self.app_key}}}
        data['messages']['msg'] = []

        # For each message do this
        for message in messages:
            # List all recipients
            to = []
            for toItem in message.to:
                to = to + [{'number': '00' + toItem}]

            # Create message container
            temp = {"allowedChannels": message.allowedChannels,
                    "from": message.from_,
                    "to": to,
                    "reference": str(uuid.uuid4()),
                    "body": {
                        "type": message.type,
                        "content": message.body
                    }
                    }

            # If message is template
            if message.template is not None:
                temp["richContent"] = {
                    "conversation": [{
                        "template":
                            {
                                "whatsapp":
                                    {
                                        "namespace": message.template.namespace,
                                        "element_name": message.template.element_name,
                                        "language":
                                            {
                                                "policy": message.template.language_policy,
                                                "code": message.template.language_code
                                            },
                                        "components": message.template.components
                                    }
                            }
                    }]
                }

            # If message is rich and no template
            if message.template is None and message.richContent is not None:
                temp["richContent"] = {
                    "conversation": [{
                        "text": message.body
                    },
                        {
                            "media": message.richContent,
                        }]
                }

            data['messages']['msg'] = data['messages']['msg'] + [temp]

        logging.info( data['messages']['msg'][0]['reference'])


        # Json encode the data
        data = json.dumps(data)
        return data


class Message:
    body = ''
    type = ''
    customgrouping3 = ''
    from_ = ''
    reference = ''
    to = []
    minimumNumberOfMessageParts = 1
    maximumNumberOfMessageParts = 8
    hybridAppKey = ''
    allowedChannels = ['SMS']
    template = None
    richContent = None
    SENDER_FALLBACK = 'cm.com'
    MESSAGEPARTS_MINIMUM = 1
    MESSAGEPARTS_MAXIMUM = 8
    RECIPIENTS_MAXIMUM = 1000

    # init function of class Message
    def __init__(self, body='', type='AUTO', from_=None, to=[]):
        self.body = body
        self.type = type
        if from_ is not None:
            self.from_ = from_
        else:
            self.from_ = self.SENDER_FALLBACK

        self.AddRecipients(recipients=to)

        self.minimumNumberOfMessageParts = self.MESSAGEPARTS_MINIMUM
        self.maximumNumberOfMessageParts = self.MESSAGEPARTS_MAXIMUM

    # add an array of recipients
    def AddRecipients(self, recipients=None):
        if recipients is None:
            recipients = []
        # check if total recipients exceeds RECIPIENTS_MAXIMUM
        if (len(self.to) + len(recipients) > self.RECIPIENTS_MAXIMUM):
            print('Maximum amount of Recipients exceeded. (' + str(self.RECIPIENTS_MAXIMUM) + ')')
        else:
            self.to = self.to + recipients
