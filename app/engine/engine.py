# -*- coding: utf-8 -*-
import logging
import time
import traceback

from app.engine import handler_list
import app.engine.daily_handler
import app.engine.user_register_handler
import app.engine.admin_register_handler

from app.model import SessionLocal
from configuration import load_config


class Engine(object):
    @staticmethod
    def run():
        while True:
            session = SessionLocal()
            keep_run = False
            try:
                for handler in handler_list:
                    handler.preprocess(session)

                for handler in handler_list:
                    result = handler.process(session)
                    keep_run = keep_run or result
                # session.commit()
            except Exception as e:
                logging.error(traceback.format_exc())
                session.rollback()
                logging.error('Engine.run error exception: {}'.format(e))

            session.close()
            if not keep_run:
                time.sleep(0.4)


if __name__ == '__main__':
    config = load_config()
    logging.basicConfig(level=config.LOG_LEVEL,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='[%Y-%m-%d %H:%M:%S]')
    Engine.run()
