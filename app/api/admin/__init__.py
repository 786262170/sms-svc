# -*- coding: utf-8 -*-
from enum import Enum

from fastapi import HTTPException
from starlette.requests import Request

from app.model.admin_user import AdminUser, AdminUserRole


def admin_login_required(request: Request, role=None):
    token = request.query_params.get('token')
    if not token:
        token = request.headers.get('token')
    if not token:
        token = request.cookies.get('token')
    if not token:
        raise HTTPException(status_code=401)
    current_user = AdminUser.verify_auth_token(request.state.db, token)
    if current_user is None:
        raise HTTPException(status_code=401)
    if role is not None:
        if (current_user.role & role) == 0 and current_user.role != AdminUserRole.SUPER:
            raise HTTPException(status_code=401)

    return current_user
