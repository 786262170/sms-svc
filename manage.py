# -*- coding: utf-8 -*-
from decimal import ROUND_DOWN, ROUND_UP, Decimal
import pycountry

from app.model import SessionLocal

db_session = SessionLocal()

country_cn_code_dict = {}


def get_one_sms_product_nx(session, channel_name, country, country_code, product_type, cost_price, profit_rate_default):
    from app.model.admin_user import AdminUser
    from app.model.sms_product import SmsProduct, SmsProductProvider

    product = session.query(SmsProduct).filter(
        SmsProduct.admin_user_id == AdminUser.ROOT_ID,
        SmsProduct.country == country,
        SmsProduct.channel_name == channel_name).first()
    if product is not None:
        product.price = round_price(cost_price * profit_rate_default)
        product.cost_price = round_price(cost_price)
    else:
        product = SmsProduct(admin_user_id=AdminUser.ROOT_ID,
                             channel_name=channel_name,
                             country=country,
                             country_code=country_code,
                             type=product_type,
                             provider=SmsProductProvider.NX.value,
                             price=round_price(
                                 cost_price * profit_rate_default),
                             cost_price=round_cost_price(cost_price))
        session.add(product)
    session.flush()


def get_sms_product_nx(session):
    import decimal
    import pandas as pd
    from app.model.sms_product import SmsProductType
    from app.model.setting import Setting

    setting = Setting.get_json(session, 'general_option')

    profit_rate_default = decimal.Decimal(
        setting['profit_rate_default']) / 100 + 1

    data = pd.read_excel('doc/NX.xlsx', header=2)
    other_code = {"Vietnam": 'VN', 'South Korea': 'KR', 'Taiwan': 'TW', 'Russia': 'RU', 'Venezuela': 'VE', 'Laos': 'LA',
                  'Iran': 'IR', 'Macau': 'MO', 'Bolivia': 'BO', 'Costa rica': 'CR', 'Tanzania': 'TZ', 'Syria': 'SY',
                  'Czech Republic': 'CZ', 'Palestinian Territory': 'PS', 'Moldova': 'MD', 'Cote d\'Ivoire': 'CI',
                  'Congo D.R.': 'CD', 'Macedonia': 'MK', 'Saint Vincent and the Grenadin': 'VC', 'Cape Verde': 'CV',
                  'Falkland Islands': 'FK', 'East Timor': 'TP', 'British Virgin Islands': 'VG',
                  'Equatorial guinea': 'GQ', 'Kosovo': 'XK', 'Guinea Bissau': 'GW'}
    countries = {}
    for country in pycountry.countries:
        countries[country.name] = country.alpha_2

    input_countries = data.iloc[:, 0].tolist()
    codes = [countries.get(country, other_code.get(country))
             for country in input_countries]

    for i in range(len(data)):
        country_cn_code_dict[data.loc[i][1]] = codes[i]
        get_one_sms_product_nx(session, 'nx_premium', codes[i], data.loc[i][2], SmsProductType.VERIFY.value,
                               decimal.Decimal(str(data.loc[i][3])), profit_rate_default)
        get_one_sms_product_nx(session, 'nx_regular', codes[i], data.loc[i][2], SmsProductType.VERIFY.value,
                               decimal.Decimal(str(data.loc[i][4])), profit_rate_default)
        get_one_sms_product_nx(session, 'nx_whosale', codes[i], data.loc[i][2], SmsProductType.MESSAGING.value,
                               decimal.Decimal(str(data.loc[i][5])), profit_rate_default)

    session.commit()


q = Decimal('1.000')


def round_cost_price(d: Decimal):
    return d.quantize(q, ROUND_DOWN)


def round_price(d: Decimal):
    return d.quantize(q, ROUND_UP)


def get_sms_product_skyline(session):
    import decimal
    import pandas as pd
    from app.model.admin_user import AdminUser
    from app.model.sms_product import SmsProduct, SmsProductType, SmsProductProvider
    from app.model.setting import Setting

    setting = Setting.get_json(session, 'general_option')

    profit_rate_default = decimal.Decimal(
        setting['profit_rate_default']) / 100 + 1

    data = pd.read_excel('doc/SKYLINE.xlsx')
    data = data.fillna('')

    other_country = {'印尼': 'ID', '澳门': 'MO', '阿联酋': 'AE', '文莱': 'BN',
                     '孟加拉': 'BD', '捷克': 'CZ', '俄罗斯联邦': 'RU', '那米比亚': 'NA', '多米尼加共和国': 'DO'}
    sms_type = None
    channel_name = None
    for i in range(len(data)):
        if data.loc[i][1] == '验证码':
            sms_type = SmsProductType.VERIFY.value
            channel_name = 'skyline_01'
            continue
        elif data.loc[i][1] == '营销':
            sms_type = SmsProductType.MESSAGING.value
            if channel_name == 'skyline_01':
                channel_name = 'skyline_02'
            elif channel_name == 'skyline_02':
                channel_name = 'skyline_03'
            else:
                raise Exception('Illegal state')
            continue
        country = country_cn_code_dict.get(
            data.loc[i][2], other_country.get(data.loc[i][2]))
        if not country or sms_type is None or sms_type is None:
            continue
        # if 3 <= i <= 61:
        #     sms_type = SmsProductType.VERIFY.value
        #     channel_name = 'skyline_01'

        # elif 65 <= i <= 81:
        #     sms_type = SmsProductType.MESSAGING.value
        #     channel_name = 'skyline_02'
        #     country = country_cn_code_dict.get(
        #         data.loc[i][2], other_country.get(data.loc[i][2]))
        # elif 84 <= i <= 137:
        #     sms_type = SmsProductType.MESSAGING.value
        #     channel_name = 'skyline_03'
        #     country = country_cn_code_dict.get(
        #         data.loc[i][2], other_country.get(data.loc[i][2]))
        # else:
        #     continue
        # if not country:
        #     raise Exception

        product = session.query(SmsProduct).filter(
            SmsProduct.admin_user_id == AdminUser.ROOT_ID,
            SmsProduct.country == country,
            SmsProduct.channel_name == channel_name).first()
        if product is not None:
            product.price = round_price(decimal.Decimal(
                data.loc[i][5]) * profit_rate_default)
            product.cost_price = round_cost_price(
                decimal.Decimal(data.loc[i][5]))
        else:
            product = SmsProduct(admin_user_id=AdminUser.ROOT_ID,
                                 channel_name=channel_name,
                                 country=country,
                                 country_code=data.loc[i][3],
                                 type=sms_type,
                                 provider=SmsProductProvider.SKYLINE.value,
                                 price=round_price(decimal.Decimal(
                                     data.loc[i][5]) * profit_rate_default),
                                 cost_price=round_cost_price(decimal.Decimal(data.loc[i][5])))
            session.add(product)
        session.flush()
    session.commit()


def get_sms_product(session):
    get_sms_product_nx(session)
    get_sms_product_skyline(session)


def modify_sms_special_check_date(session):
    import datetime
    from app.model.sms_product import SmsSpecialCheck

    q = session.query(SmsSpecialCheck).filter().all()
    for item in q:
        now = datetime.datetime(2021, 7, 26)
        check = session.query(SmsSpecialCheck).get(item.id)
        check.date = now
        session.commit()


def db_initialize(session):
    from app.model.admin_user import AdminUser
    from app.model.user import User
    from app.model.setting import Setting
    from app.model.sms_product import SmsChannel, SmsSpecialCheck

    AdminUser.initialize(session)
    User.initialize(session)
    Setting.update_default_options(session)
    SmsChannel.initialize(session)
    SmsSpecialCheck.initialize(session)

    get_sms_product(session)
    # modify_sms_special_check_date(session)


if __name__ == '__main__':
    db_initialize(db_session)
