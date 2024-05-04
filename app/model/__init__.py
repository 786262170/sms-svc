# -*- coding: utf-8 -*-
import datetime
import uuid
import time
import random

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from math import ceil
from sqlalchemy import create_engine, Column, DateTime, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Query

from configuration import load_config

app_config = load_config()
SQLALCHEMY_DATABASE_URL = app_config.SQLALCHEMY_DATABASE_URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=app_config.SQLALCHEMY_POOL_RECYCLE,
    pool_size=app_config.SQLALCHEMY_POOL_SIZE,
    echo=app_config.SQLALCHEMY_ECHO
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Pagination(object):
    """
    分页对象
    """

    def __init__(self, query, page, per_page, total, items):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        return self.page > 1

    def next(self, error_out=False):
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def next_num(self):
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and \
                     num < self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def paginate(self, page=None, per_page=None, error_out=False):
    """
    分页函数
    :param self:
    :param page:
    :param per_page:
    :param error_out:
    :return:
    """

    if page is None:
        page = 1

    if per_page is None:
        per_page = 20

    if error_out and page < 1:
        raise HTTPException(status_code=404)

    items = self.limit(per_page).offset((page - 1) * per_page).all()

    if not items and page != 1 and error_out:
        raise HTTPException(status_code=404)

    if page == 1 and len(items) < per_page:
        total = len(items)
    else:
        total = self.order_by(None).count()

    return Pagination(self, page, per_page, total, items)


Query.paginate = paginate  # 在原查询类上加上分页方法


def generate_timestamp_id():
    return str(int(time.time()) * 1000000 + random.randint(100000, 999999))


# 时间转换为时间戳
def datetime_to_timestamp(date_time):
    return int(date_time.timestamp())


# 时间戳转换为时间
def timestamp_to_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


# 从str日期转datetime
def datetime_from_str_time(str_time, format_str='%Y-%m-%d'):
    return datetime.datetime.strptime(str(str_time), format_str)


# 从datetime转str日期
def datetime_to_str_time(date_time, format_str='%Y-%m-%d'):
    return date_time.strftime(format_str)


# 时间的日期
def date_datetime(date_time):
    begin = datetime.datetime(year=date_time.year,
                              month=date_time.month,
                              day=date_time.day)
    return begin


# 当天起始、结束时间
def day_datetime(date_time):
    begin = datetime.datetime(year=date_time.year,
                              month=date_time.month,
                              day=date_time.day)
    end = begin + datetime.timedelta(days=1)
    return begin, end


# 当天起始、结束时间
def month_datetime(date_time):
    begin = datetime.datetime(year=date_time.year,
                              month=date_time.month,
                              day=1)
    end = begin + relativedelta(months=1)
    return begin, end


class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime,
                        default=datetime.datetime.now,
                        nullable=False)
    updated_at = Column(DateTime,
                        default=datetime.datetime.now,
                        onupdate=datetime.datetime.now,
                        nullable=False)

    @property
    def created_timestamp(self):
        return datetime_to_timestamp(self.created_at)

    @property
    def updated_timestamp(self):
        return datetime_to_timestamp(self.updated_at)


class UuidBase(BaseModel):
    __abstract__ = True

    id = Column(String(36), default=uuid.uuid4, primary_key=True)


class AutoIncrementBase(BaseModel):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


import app.model.pin_code
import app.model.setting
import app.model.schedule_task
import app.model.admin_user
import app.model.user
import app.model.application
import app.model.contact
import app.model.message
import app.model.sms_product
import app.model.sms_user
import app.model.wallet_order
