import json

import sqlalchemy as sa

from app.model import Base


class Setting(Base):
    __tablename__ = 'setting'

    name = sa.Column(sa.String(50), primary_key=True)
    value = sa.Column(sa.Text, nullable=False)
    title = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text, nullable=False)

    GENERAL_OPTION = {
        'profit_rate_default': '10',
        'recharge_fee_rate': '2',
    }

    GENERAL_OPTION_DESCRIPTION = {
        'profit_rate_default': '默认收益率 %',
        'recharge_fee_rate': '充值手续费率 %',
    }
    DEFAULT_OPTIONS = [
        ('general_option',
         json.dumps(GENERAL_OPTION),
         u'常规选项',
         json.dumps(GENERAL_OPTION_DESCRIPTION)),
    ]

    @staticmethod
    def update_default_options(session):
        for name, value, title, description in Setting.DEFAULT_OPTIONS:
            setting = session.query(Setting).get(name)
            # if setting:
            #     setting.title = title
            #     setting.description = description
            #     runtime_json = json.loads(setting.value)
            #     default_json = json.loads(value)
            #     for k, v in default_json.items():
            #         if k not in runtime_json:
            #             runtime_json[k] = v
            #     setting.value = json.dumps(runtime_json)
            # else:
            if not setting:
                setting = Setting(name=name, value=value, title=title, description=description)
                session.add(setting)
        session.commit()

    @staticmethod
    def get_json(session, name):

        data = session.query(Setting).get(name).value
        return json.loads(data)

    @staticmethod
    def set_json(name, option):
        json_str = json.dumps(option)
        return json_str
