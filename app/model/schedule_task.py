# -*- coding: utf-8 -*-
from sqlalchemy.orm import relationship

from app.model import AutoIncrementBase, day_datetime
import sqlalchemy as sa


class ScheduleTaskBase(AutoIncrementBase):
    __abstract__ = True

    status = sa.Column(sa.SmallInteger, default=0)  # 0 未处理  1 已处理
    processed_at = sa.Column(sa.DateTime)

    def done(self, processed_at):
        self.status = 1
        self.processed_at = processed_at

    @classmethod
    def peek(cls, session):
        return session.query(cls).filter_by(status=0).order_by(cls.id).first()


class DailyScheduleTask(ScheduleTaskBase):
    __tablename__ = 'daily_schedule_task'

    timestamp = sa.Column(sa.Integer, nullable=False, unique=True)

    @staticmethod
    def generate_daily_schedule_task(session, now):
        begin, end = day_datetime(now)
        timestamp = begin.timestamp()
        if session.query(DailyScheduleTask).filter_by(timestamp=timestamp).first():
            return
        task = DailyScheduleTask(timestamp=timestamp)
        session.add(task)
        session.commit()


class AdminRegisterScheduleTask(ScheduleTaskBase):
    __tablename__ = 'admin_register_schedule_task'

    admin_user_id = sa.Column(sa.String(36), sa.ForeignKey('admin_user.id'), nullable=False, unique=True)

    admin_user = relationship('AdminUser', foreign_keys=[admin_user_id])


class UserRegisterScheduleTask(ScheduleTaskBase):
    __tablename__ = 'user_register_schedule_task'

    user_id = sa.Column(sa.String(36), sa.ForeignKey('user.id'), nullable=False, unique=True)

    user = relationship('User', foreign_keys=[user_id])

