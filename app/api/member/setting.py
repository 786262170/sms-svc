from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import get_db
from app.model.setting import Setting

router = APIRouter()


@router.get('/')
def get_setting(session: Session = Depends(get_db)):
    return Setting.get_json(session, 'general_option')
