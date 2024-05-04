# -*- coding: utf-8 -*-
import uvicorn

from app import create_api
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.api import BsException, BsExceptionEnum, BsExceptionWithNumbers
from app.model import SessionLocal

api = create_api()

# def custom_openapi():
#     if api.openapi_schema:
#         return api.openapi_schema
#     config = load_config()
#
#     openapi_schema = get_openapi(
#         title=config.PRODUCT_NAME,
#         version="2.5.0",
#         routes=api.routes)
#     api.openapi_schema = openapi_schema
#
#     return api.openapi_schema
#
#
# api.openapi = custom_openapi
origins = [
    "https://icaisms-api.staging.icaicloud.com",
    "https://icaisms-dashboard.staging.icaicloud.com",
    "http://localhost",
    "https://cmessages.com",
    "https://dashboard.cmessages.com",
    "https://staging.dashboard.cmessages.com",
    "https://console.cmessages.com",
    "https://staging.console.cmessages.com",
    "http://localhost:8080",
    "https://127.0.0.1:1025",
    "https://127.0.0.1:1024"
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


# @api.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     message = {}
#     for item in exc.errors():
#         message[item['loc'][-1]] = item['msg']
#     return JSONResponse(
#         status_code=400,
#         content={"code": BsExceptionEnum.PARAMETER_ERROR.value, 'message': message},
#     )


@api.exception_handler(BsException)
async def unicorn_exception_handler(request: Request, exc: BsException):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, 'message': exc.message},
    )


@api.exception_handler(BsExceptionWithNumbers)
async def unicorn_exception_handler(request: Request, exc: BsExceptionWithNumbers):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, 'message': exc.message, 'numbers': exc.numbers},
    )


if __name__ == '__main__':
    uvicorn.run('run:api', host='0.0.0.0', port=8085,
                log_level='debug', reload=True)
