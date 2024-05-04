# -*- coding: utf-8 -*-
import logging
import time
import traceback
import sqlalchemy as sa

from app.model import SessionLocal
from app.model.user import User
from configuration import load_config


class Engine(object):
    @staticmethod
    def run():
        while True:
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.usdt_address.is_(None)).first()
                if not user:
                    session.close()
                    time.sleep(1)
                else:
                    if user.usdt_address is None:
                        user.usdt_address = user.create_address('USDT', user.usdt_number)
                    session.commit()
            except Exception as e:
                logging.error(traceback.format_exc())
                session.rollback()
                logging.error('Engine.run error exception: {}'.format(e))
                time.sleep(1)

            session.close()


if __name__ == '__main__':
    config = load_config()
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='[%Y-%m-%d %H:%M:%S]')
    Engine.run()
