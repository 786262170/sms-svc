# -*- coding: utf-8 -*-
import datetime
from app.model.schedule_task import ScheduleTaskBase

class StandardHandler(object):
    def __init__(self, schedule_task_class):
        assert issubclass(schedule_task_class, ScheduleTaskBase)
        self.model_class = schedule_task_class

    def get_schedule_task_handlers(self):
        raise NotImplemented("Must implement it")

    def preprocess(self, session):
        return

    def process(self, session):  # 返回 True 表示继续执行; 返回 False 表示暂停执行
        task = self.model_class.peek(session)
        if not task:
            return False
        handlers = self.get_schedule_task_handlers()
        keep_run = False
        for handler in handlers:
            result = handler(task, session)
            keep_run = keep_run or result
        task.done(datetime.datetime.now())
        session.commit()
        return keep_run


handler_list: "list[StandardHandler]" = []
