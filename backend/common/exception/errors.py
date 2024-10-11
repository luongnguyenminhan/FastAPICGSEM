#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global business exception class

When a business code execution exception occurs, you can use raise xxxError to trigger an internal error. It tries to implement exceptions with background tasks, but it is not suitable for **custom response status codes**.
If you need to use **custom response status codes**, you can directly return response_base.fail(res=CustomResponseCode.xxx).
"""  # noqa: E501

from typing import Any

from fastapi import HTTPException
from starlette.background import BackgroundTask

from backend.common.response.response_code import CustomErrorCode, StandardResponseCode


class BaseExceptionMixin(Exception):
    code: int

    def __init__(self, *, msg: str = None, data: Any = None, background: BackgroundTask | None = None):
        self.msg = msg
        self.data = data
        # The original background task: https://www.starlette.io/background/
        self.background = background


class HTTPError(HTTPException):
    def __init__(self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None):
        super().__init__(status_code=code, detail=msg, headers=headers)


class CustomError(BaseExceptionMixin):
    def __init__(self, *, error: CustomErrorCode, data: Any = None, background: BackgroundTask | None = None):
        self.code = error.code
        super().__init__(msg=error.msg, data=data, background=background)


class RequestError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_400

    def __init__(self, *, msg: str = 'Bad Request', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class ForbiddenError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_403

    def __init__(self, *, msg: str = 'Forbidden', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class NotFoundError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_404

    def __init__(self, *, msg: str = 'Not Found', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class ServerError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_500

    def __init__(
        self, *, msg: str = 'Internal Server Error', data: Any = None, background: BackgroundTask | None = None
    ):
        super().__init__(msg=msg, data=data, background=background)


class GatewayError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_502

    def __init__(self, *, msg: str = 'Bad Gateway', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class AuthorizationError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_401

    def __init__(self, *, msg: str = 'Permission Denied', data: Any = None, background: BackgroundTask | None = None):
        super().__init__(msg=msg, data=data, background=background)


class TokenError(HTTPError):
    code = StandardResponseCode.HTTP_401

    def __init__(self, *, msg: str = 'Not Authenticated', headers: dict[str, Any] | None = None):
        super().__init__(code=self.code, msg=msg, headers=headers or {'WWW-Authenticate': 'Bearer'})