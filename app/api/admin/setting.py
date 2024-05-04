import json
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import GetSession
from app.api.admin import admin_login_required
from app.model.setting import Setting

router = APIRouter()


@router.get('/')
def get_setting(session: Session = Depends(GetSession(admin_login_required))):
    return Setting.get_json(session, 'general_option')


#   设置请求类
class SettingRequest(BaseModel):
    profit_rate: int = None


@router.put('/')
def put_setting(data: SettingRequest,
                session: Session = Depends(GetSession(admin_login_required))):
    """修改系统设置"""
    setting = session.query(Setting).get('general_option')
    option = json.loads(setting.value)

    request_data = data.dict()
    for k, v in request_data.items():
        if v is not None:
            if type(v).__name__ == 'dict':
                for v_k, v_v in v.items():
                    v_v = str(v_v) if v_k == 'value' else v_v
                    option[k][v_k] = v_v
            elif type(v).__name__ == 'Decimal':
                option[k] = str(v)
            else:
                option[k] = v

    setting.value = json.dumps(option)

    session.commit()
    return option
