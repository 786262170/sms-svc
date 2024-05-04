# -*- coding: utf-8 -*-
from fastapi import HTTPException
from starlette.requests import Request

from app.model.user import User


def member_login_required(request: Request):
    session = request.state.db
    token = request.query_params.get('token')
    if not token:
        token = request.cookies.get('token')
    if not token:
        token = request.headers.get('token')
    if not token:
        raise HTTPException(status_code=401)

    current_user = User.verify_auth_token(session, token)
    if current_user is None:
        raise HTTPException(status_code=401)
    return current_user


def member_not_verify_again_required(request: Request):
    session = request.state.db
    token = request.query_params.get('token')
    if not token:
        token = request.cookies.get('token')
    if not token:
        token = request.headers.get('token')
    if not token:
        raise HTTPException(status_code=401)

    current_user = User.verify_auth_token(session, token, verify_again=False)
    if current_user is None:
        raise HTTPException(status_code=401)
    return current_user


def get_country_name(country_code: str, lang: str = 'cn'):
    return country_dict[country_code][lang] if country_code in country_dict else None


country_dict = {
    'AX': {'cn': '奥兰群岛', 'en': 'Aland Islands'}, 'AL': {'cn': '阿尔巴尼亚', 'en': 'Albania'},
    'DZ': {'cn': '阿尔及利亚', 'en': 'Algeria'}, 'AS': {'cn': '美属萨摩亚', 'en': 'American Samoa'},
    'AD': {'cn': '安道尔', 'en': 'Andorra'}, 'AO': {'cn': '安哥拉', 'en': 'Angola'},
    'AI': {'cn': '安圭拉', 'en': 'Anguilla'},
    'AQ': {'cn': '南极洲', 'en': 'Antarctica'}, 'AG': {'cn': '安提瓜和巴布达', 'en': 'Antigua and Barbuda'},
    'AR': {'cn': '阿根廷', 'en': 'Argentina'}, 'AM': {'cn': '亚美尼亚', 'en': 'Armenia'},
    'AW': {'cn': '阿鲁巴', 'en': 'Aruba'},
    'AU': {'cn': '澳大利亚', 'en': 'Australia'}, 'AT': {'cn': '奥地利', 'en': 'Austria'},
    'AZ': {'cn': '阿塞拜疆', 'en': 'Azerbaijan'}, 'BS': {'cn': '巴哈马', 'en': 'Bahamas (The)'},
    'BH': {'cn': '巴林', 'en': 'Bahrain'}, 'BD': {'cn': '孟加拉国', 'en': 'Bangladesh'},
    'BB': {'cn': '巴巴多斯', 'en': 'Barbados'},
    'BY': {'cn': '白俄罗斯', 'en': 'Belarus'}, 'BE': {'cn': '比利时', 'en': 'Belgium'},
    'BZ': {'cn': '伯利兹', 'en': 'Belize'},
    'BJ': {'cn': '贝宁', 'en': 'Benin'}, 'BM': {'cn': '百慕大', 'en': 'Bermuda'},
    'BT': {'cn': '不丹', 'en': 'Bhutan'},
    'BO': {'cn': '玻利维亚', 'en': 'Bolivia'}, 'BA': {'cn': '波黑', 'en': 'Bosnia and Herzegovina'},
    'BW': {'cn': '博茨瓦纳', 'en': 'Botswana'}, 'BV': {'cn': '布维岛', 'en': 'Bouvet Island'},
    'BR': {'cn': '巴西', 'en': 'Brazil'},
    'IO': {'cn': '英属印度洋领地', 'en': 'British Indian Ocean Territory (the)'},
    'BN': {'cn': '文莱', 'en': 'Brunei Darussalam'},
    'BG': {'cn': '保加利亚', 'en': 'Bulgaria'}, 'BF': {'cn': '布基纳法索', 'en': 'Burkina Faso'},
    'BI': {'cn': '布隆迪', 'en': 'Burundi'}, 'KH': {'cn': '柬埔寨', 'en': 'Cambodia'},
    'CM': {'cn': '喀麦隆', 'en': 'Cameroon'},
    'CA': {'cn': '加拿大', 'en': 'Canada'}, 'CV': {'cn': '佛得角', 'en': 'Cape Verde'},
    'KY': {'cn': '开曼群岛', 'en': 'Cayman Islands (the)'},
    'CF': {'cn': '中非', 'en': 'Central African Republic (the)'},
    'TD': {'cn': '乍得', 'en': 'Chad'}, 'CL': {'cn': '智利', 'en': 'Chile'}, 'CN': {'cn': '中国', 'en': 'China'},
    'CX': {'cn': '圣诞岛', 'en': 'Christmas Island'},
    'CC': {'cn': '科科斯（基林）群岛', 'en': 'Cocos (Keeling) Islands (the)'},
    'CO': {'cn': '哥伦比亚', 'en': 'Colombia'}, 'KM': {'cn': '科摩罗', 'en': 'Comoros'},
    'CG': {'cn': '刚果（布）', 'en': 'Congo'},
    'CD': {'cn': '刚果（金）', 'en': 'Congo (the Democratic Republic of the)'},
    'CK': {'cn': '库克群岛', 'en': 'Cook Islands (the)'}, 'CR': {'cn': '哥斯达黎加', 'en': 'Costa Rica'},
    'CI': {'cn': '科特迪瓦', 'en': "Côte d'Ivoire"}, 'HR': {'cn': '克罗地亚', 'en': 'Croatia'},
    'CU': {'cn': '古巴', 'en': 'Cuba'},
    'CY': {'cn': '塞浦路斯', 'en': 'Cyprus'}, 'CZ': {'cn': '捷克', 'en': 'Czech Republic (the)'},
    'DK': {'cn': '丹麦', 'en': 'Denmark'}, 'DJ': {'cn': '吉布提', 'en': 'Djibouti'},
    'DM': {'cn': '多米尼克', 'en': 'Dominica'},
    'DO': {'cn': '多米尼加', 'en': 'Dominican Republic (the)'}, 'EC': {'cn': '厄瓜多尔', 'en': 'Ecuador'},
    'EG': {'cn': '埃及', 'en': 'Egypt'}, 'SV': {'cn': '萨尔瓦多', 'en': 'El Salvador'},
    'GQ': {'cn': '赤道几内亚', 'en': 'Equatorial Guinea'}, 'ER': {'cn': '厄立特里亚', 'en': 'Eritrea'},
    'EE': {'cn': '爱沙尼亚', 'en': 'Estonia'}, 'ET': {'cn': '埃塞俄比亚', 'en': 'Ethiopia'},
    'FK': {'cn': '福克兰群岛（马尔维纳斯）', 'en': 'Falkland Islands (the) [Malvinas]'},
    'FO': {'cn': '法罗群岛', 'en': 'Faroe Islands (the)'}, 'FJ': {'cn': '斐济', 'en': 'Fiji'},
    'FI': {'cn': '芬兰', 'en': 'Finland'}, 'FR': {'cn': '法国', 'en': 'France'},
    'GF': {'cn': '法属圭亚那', 'en': 'French Guiana'},
    'PF': {'cn': '法属波利尼西亚', 'en': 'French Polynesia'},
    'TF': {'cn': '法属南部领地', 'en': 'French Southern Territories (the)'},
    'GA': {'cn': '加蓬', 'en': 'Gabon'}, 'GM': {'cn': '冈比亚', 'en': 'Gambia (The)'},
    'GE': {'cn': '格鲁吉亚', 'en': 'Georgia'},
    'DE': {'cn': '德国', 'en': 'Germany'}, 'GH': {'cn': '加纳', 'en': 'Ghana'},
    'GI': {'cn': '直布罗陀', 'en': 'Gibraltar'},
    'GR': {'cn': '希腊', 'en': 'Greece'}, 'GL': {'cn': '格陵兰', 'en': 'Greenland'},
    'GD': {'cn': '格林纳达', 'en': 'Grenada'},
    'GP': {'cn': '瓜德罗普', 'en': 'Guadeloupe'}, 'GU': {'cn': '关岛', 'en': 'Guam'},
    'GT': {'cn': '危地马拉', 'en': 'Guatemala'},
    'GG': {'cn': '格恩西岛', 'en': 'Guernsey'}, 'GN': {'cn': '几内亚', 'en': 'Guinea'},
    'GW': {'cn': '几内亚比绍', 'en': 'Guinea-Bissau'}, 'GY': {'cn': '圭亚那', 'en': 'Guyana'},
    'HT': {'cn': '海地', 'en': 'Haiti'},
    'HM': {'cn': '赫德岛和麦克唐纳岛', 'en': 'Heard Island and McDonald Islands'},
    'VA': {'cn': '梵蒂冈', 'en': 'Holy See (the) [Vatican City State]'},
    'HN': {'cn': '洪都拉斯', 'en': 'Honduras'},
    'HK': {'cn': '香港', 'en': 'Hong Kong'}, 'HU': {'cn': '匈牙利', 'en': 'Hungary'},
    'IS': {'cn': '冰岛', 'en': 'Iceland'},
    'IN': {'cn': '印度', 'en': 'India'}, 'ID': {'cn': '印度尼西亚', 'en': 'Indonesia'},
    'IR': {'cn': '伊朗', 'en': 'Iran (the Islamic Republic of)'}, 'IQ': {'cn': '伊拉克', 'en': 'Iraq'},
    'IE': {'cn': '爱尔兰', 'en': 'Ireland'}, 'IM': {'cn': '英国属地曼岛', 'en': 'Isle of Man'},
    'IL': {'cn': '以色列', 'en': 'Israel'},
    'IT': {'cn': '意大利', 'en': 'Italy'}, 'JM': {'cn': '牙买加', 'en': 'Jamaica'},
    'JP': {'cn': '日本', 'en': 'Japan'},
    'JE': {'cn': '泽西岛', 'en': 'Jersey'}, 'JO': {'cn': '约旦', 'en': 'Jordan'},
    'KZ': {'cn': '哈萨克斯坦', 'en': 'Kazakhstan'},
    'KE': {'cn': '肯尼亚', 'en': 'Kenya'}, 'KI': {'cn': '基里巴斯', 'en': 'Kiribati'},
    'KP': {'cn': '朝鲜', 'en': "Korea (the Democratic People's Republic of)"},
    'KR': {'cn': '韩国', 'en': 'Korea (the Republic of)'}, 'KW': {'cn': '科威特', 'en': 'Kuwait'},
    'KG': {'cn': '吉尔吉斯斯坦', 'en': 'Kyrgyzstan'},
    'LA': {'cn': '老挝', 'en': "Lao People's Democratic Republic (the)"},
    'LV': {'cn': '拉脱维亚', 'en': 'Latvia'}, 'LB': {'cn': '黎巴嫩', 'en': 'Lebanon'},
    'LS': {'cn': '莱索托', 'en': 'Lesotho'},
    'LR': {'cn': '利比里亚', 'en': 'Liberia'}, 'LY': {'cn': '利比亚', 'en': 'Libyan Arab Jamahiriya (the)'},
    'LI': {'cn': '列支敦士登', 'en': 'Liechtenstein'}, 'LT': {'cn': '立陶宛', 'en': 'Lithuania'},
    'LU': {'cn': '卢森堡', 'en': 'Luxembourg'}, 'MO': {'cn': '澳门', 'en': 'Macao'},
    'MK': {'cn': '前南马其顿', 'en': 'Macedonia (the former Yugoslav Republic of)'},
    'MG': {'cn': '马达加斯加', 'en': 'Madagascar'},
    'MW': {'cn': '马拉维', 'en': 'Malawi'}, 'MY': {'cn': '马来西亚', 'en': 'Malaysia'},
    'MV': {'cn': '马尔代夫', 'en': 'Maldives'},
    'ML': {'cn': '马里', 'en': 'Mali'}, 'MT': {'cn': '马耳他', 'en': 'Malta'},
    'MH': {'cn': '马绍尔群岛', 'en': 'Marshall Islands (the)'}, 'MQ': {'cn': '马提尼克', 'en': 'Martinique'},
    'MR': {'cn': '毛利塔尼亚', 'en': 'Mauritania'}, 'MU': {'cn': '毛里求斯', 'en': 'Mauritius'},
    'YT': {'cn': '马约特', 'en': 'Mayotte'}, 'MX': {'cn': '墨西哥', 'en': 'Mexico'},
    'FM': {'cn': '密克罗尼西亚联邦', 'en': 'Micronesia (the Federated States of)'},
    'MD': {'cn': '摩尔多瓦', 'en': 'Moldova (the Republic of)'}, 'MC': {'cn': '摩纳哥', 'en': 'Monaco'},
    'MN': {'cn': '蒙古', 'en': 'Mongolia'}, 'ME': {'cn': '黑山', 'en': 'Montenegro'},
    'MS': {'cn': '蒙特塞拉特', 'en': 'Montserrat'}, 'MA': {'cn': '摩洛哥', 'en': 'Morocco'},
    'MZ': {'cn': '莫桑比克', 'en': 'Mozambique'}, 'MM': {'cn': '缅甸', 'en': 'Myanmar'},
    'NA': {'cn': '纳米比亚', 'en': 'Namibia'},
    'NR': {'cn': '瑙鲁', 'en': 'Nauru'}, 'NP': {'cn': '尼泊尔', 'en': 'Nepal'},
    'NL': {'cn': '荷兰', 'en': 'Netherlands (the)'},
    'AN': {'cn': '荷属安的列斯', 'en': 'Netherlands Antilles (the)'},
    'NC': {'cn': '新喀里多尼亚', 'en': 'New Caledonia'},
    'NZ': {'cn': '新西兰', 'en': 'New Zealand'}, 'NI': {'cn': '尼加拉瓜', 'en': 'Nicaragua'},
    'NE': {'cn': '尼日尔', 'en': 'Niger (the)'}, 'NG': {'cn': '尼日利亚', 'en': 'Nigeria'},
    'NU': {'cn': '纽埃', 'en': 'Niue'},
    'NF': {'cn': '诺福克岛', 'en': 'Norfolk Island'},
    'MP': {'cn': '北马里亚纳', 'en': 'Northern Mariana Islands (the)'},
    'NO': {'cn': '挪威', 'en': 'Norway'}, 'OM': {'cn': '阿曼', 'en': 'Oman'},
    'PK': {'cn': '巴基斯坦', 'en': 'Pakistan'},
    'PW': {'cn': '帕劳', 'en': 'Palau'}, 'PS': {'cn': '巴勒斯坦', 'en': 'Palestinian Territory (the Occupied)'},
    'PA': {'cn': '巴拿马', 'en': 'Panama'}, 'PG': {'cn': '巴布亚新几内亚', 'en': 'Papua New Guinea'},
    'PY': {'cn': '巴拉圭', 'en': 'Paraguay'}, 'PE': {'cn': '秘鲁', 'en': 'Peru'},
    'PH': {'cn': '菲律宾', 'en': 'Philippines (the)'}, 'PN': {'cn': '皮特凯恩', 'en': 'Pitcairn'},
    'PL': {'cn': '波兰', 'en': 'Poland'}, 'PT': {'cn': '葡萄牙', 'en': 'Portugal'},
    'PR': {'cn': '波多黎各', 'en': 'Puerto Rico'},
    'QA': {'cn': '卡塔尔', 'en': 'Qatar'}, 'RE': {'cn': '留尼汪', 'en': 'Réunion'},
    'RO': {'cn': '罗马尼亚', 'en': 'Romania'},
    'RU': {'cn': '俄罗斯联邦', 'en': 'Russian Federation (the)'}, 'RW': {'cn': '卢旺达', 'en': 'Rwanda'},
    'SH': {'cn': '圣赫勒拿', 'en': 'Saint Helena'}, 'KN': {'cn': '圣基茨和尼维斯', 'en': 'Saint Kitts and Nevis'},
    'LC': {'cn': '圣卢西亚', 'en': 'Saint Lucia'}, 'PM': {'cn': '圣皮埃尔和密克隆', 'en': 'Saint Pierre and Miquelon'},
    'VC': {'cn': '圣文森特和格林纳丁斯', 'en': 'Saint Vincent and the Grenadines'},
    'WS': {'cn': '萨摩亚', 'en': 'Samoa'},
    'SM': {'cn': '圣马力诺', 'en': 'San Marino'}, 'ST': {'cn': '圣多美和普林西比', 'en': 'Sao Tome and Principe'},
    'SA': {'cn': '沙特阿拉伯', 'en': 'Saudi Arabia'}, 'SN': {'cn': '塞内加尔', 'en': 'Senegal'},
    'RS': {'cn': '塞尔维亚', 'en': 'Serbia'}, 'SC': {'cn': '塞舌尔', 'en': 'Seychelles'},
    'SL': {'cn': '塞拉利昂', 'en': 'Sierra Leone'}, 'SG': {'cn': '新加坡', 'en': 'Singapore'},
    'SK': {'cn': '斯洛伐克', 'en': 'Slovakia'}, 'SI': {'cn': '斯洛文尼亚', 'en': 'Slovenia'},
    'SB': {'cn': '所罗门群岛', 'en': 'Solomon Islands (the)'}, 'SO': {'cn': '索马里', 'en': 'Somalia'},
    'ZA': {'cn': '南非', 'en': 'South Africa'},
    'GS': {'cn': '南乔治亚岛和南桑德韦奇岛', 'en': 'South Georgia and the South Sandwich Islands'},
    'ES': {'cn': '西班牙', 'en': 'Spain'},
    'LK': {'cn': '斯里兰卡', 'en': 'Sri Lanka'}, 'SD': {'cn': '苏丹', 'en': 'Sudan (the)'},
    'SR': {'cn': '苏里南', 'en': 'Suriname'}, 'SJ': {'cn': '斯瓦尔巴岛和扬马延岛', 'en': 'Svalbard and Jan Mayen'},
    'SZ': {'cn': '斯威士兰', 'en': 'Swaziland'}, 'SE': {'cn': '瑞典', 'en': 'Sweden'},
    'CH': {'cn': '瑞士', 'en': 'Switzerland'},
    'SY': {'cn': '叙利亚', 'en': 'Syrian Arab Republic (the)'},
    'TW': {'cn': '台湾', 'en': 'Taiwan (Province of China)'},
    'TJ': {'cn': '塔吉克斯坦', 'en': 'Tajikistan'}, 'TZ': {'cn': '坦桑尼亚', 'en': 'Tanzania,United Republic of'},
    'TH': {'cn': '泰国', 'en': 'Thailand'}, 'TL': {'cn': '东帝汶', 'en': 'Timor-Leste'},
    'TG': {'cn': '多哥', 'en': 'Togo'},
    'TK': {'cn': '托克劳', 'en': 'Tokelau'}, 'TO': {'cn': '汤加', 'en': 'Tonga'},
    'TT': {'cn': '特立尼达和多巴哥', 'en': 'Trinidad and Tobago'}, 'TN': {'cn': '突尼斯', 'en': 'Tunisia'},
    'TR': {'cn': '土耳其', 'en': 'Turkey'}, 'TM': {'cn': '土库曼斯坦', 'en': 'Turkmenistan'},
    'TC': {'cn': '特克斯和凯科斯群岛', 'en': 'Turks and Caicos Islands (the)'}, 'TV': {'cn': '图瓦卢', 'en': 'Tuvalu'},
    'UG': {'cn': '乌干达', 'en': 'Uganda'}, 'UA': {'cn': '乌克兰', 'en': 'Ukraine'},
    'AE': {'cn': '阿联酋', 'en': 'United Arab Emirates (the)'},
    'GB': {'cn': '英国', 'en': 'United Kingdom (the)'},
    'US': {'cn': '美国', 'en': 'United States (the)'},
    'UM': {'cn': '美国本土外小岛屿', 'en': 'United States Minor Outlying Islands (the)'},
    'UY': {'cn': '乌拉圭', 'en': 'Uruguay'},
    'UZ': {'cn': '乌兹别克斯坦', 'en': 'Uzbekistan'}, 'VU': {'cn': '瓦努阿图', 'en': 'Vanuatu'},
    'VE': {'cn': '委内瑞拉', 'en': 'Venezuela'}, 'VN': {'cn': '越南', 'en': 'Viet Nam'},
    'VG': {'cn': '英属维尔京群岛', 'en': 'Virgin Islands (British)'},
    'VI': {'cn': '美属维尔京群岛', 'en': 'Virgin Islands (U.S.)'},
    'WF': {'cn': '瓦利斯和富图纳', 'en': 'Wallis and Futuna'}, 'EH': {'cn': '西撒哈拉', 'en': 'Western Sahara'},
    'YE': {'cn': '也门', 'en': 'Yemen'}, 'ZM': {'cn': '赞比亚', 'en': 'Zambia'},
    'ZW': {'cn': '津巴布韦', 'en': 'Zimbabwe'},
    'AF': {'cn': '阿富汗', 'en': 'Afghanistan'},
    'SS': {'cn': '南苏丹', 'en': 'South Sudan'},
    'TP': {'cn': '圣多美和普林西比', 'en': 'República Democrática de São Tomé e Príncipe'},
    'XK': {'cn': '科索沃', 'en': 'Republika Kosovo'}
}
