# -*- coding: utf-8 -*-
import logging
from sdk import SmsDriver
from sdk.cmcom import CmcomSms
from sdk.nxcloud import NXCloudSms
from sdk.skyline import SkyLineSms
from sdk.util import divide_chunks


class SmsApi(object):
    def __init__(self, provider, app_id, app_key):
        drv = [
            NXCloudSms,
            SkyLineSms,
            CmcomSms,
        ]

        self.handle:SmsDriver = drv[provider](app_id, app_key)

    # return list(dict(phone, id)))
    def send_sms(self, phone: list, content) -> list:
        return self.handle.send_sms(phone, content)

    # return list(dict(id, status)))
    def get_status(self, ids: list) -> list:
        return self.handle.get_status(ids)

    def send_sms_chunked(self, phone: "list[str]", content: str) -> list:
        chunks = divide_chunks(phone, self.handle.send_limit)
        result = []
        for phone_chunk in chunks:
            result += self.send_sms(phone_chunk, content)
        sent_numbers = set()
        for result_dict in result:
            sent_numbers.add(result_dict["phone"])
        for number in phone:
            if number not in sent_numbers:
                result.append({"phone": number, "id": None})
                logging.info("[sms_api] %s not sent", number)
        return result

    def get_status_chunked(self, ids: "list[str]") -> list:
        chunks = divide_chunks(ids, self.handle.status_limit)
        result = []
        for id_chunk in chunks:
            result += self.get_status(id_chunk)
        return result