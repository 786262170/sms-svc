# -*- coding: utf-8 -*-
import datetime

from app.engine import handler_list, StandardHandler
from app.model.schedule_task import DailyScheduleTask
from app.model.user import User


def expired_handler(task, session):
    # User.calc_daily(session)
    return False


class DailyHandler(StandardHandler):
    def __init__(self):
        super(DailyHandler, self).__init__(DailyScheduleTask)

    def preprocess(self, session):
        DailyScheduleTask.generate_daily_schedule_task(session, datetime.datetime.now())

    def get_schedule_task_handlers(self):
        return [expired_handler]


handler_list.append(DailyHandler())
