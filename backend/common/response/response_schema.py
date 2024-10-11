#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any

from fastapi import Response
from pydantic import BaseModel, ConfigDict

from backend.common.response.response_code import CustomResponse, CustomResponseCode
from backend.core.conf import settings
from backend.utils.serializers import MsgSpecJSONResponse

_ExcludeData = set[int | str] | dict[int | str, Any]

__all__ = ['ResponseModel', 'response_base']


class ResponseModel(BaseModel):
    """
    Unified response model

    E.g. ::

        @router.get('/test', response_model=ResponseModel)
        def test():
            return ResponseModel(data={'test': 'test'})


        @router.get('/test')
        def test() -> ResponseModel:
            return ResponseModel(data={'test': 'test'})


        @router.get('/test')
        def test() -> ResponseModel:
            res = CustomResponseCode.HTTP_200
            return ResponseModel(code=res.code, msg=res.msg, data={'test': 'test'})
    """

    # TODO: json_encoders configuration is invalid: https://github.com/tiangolo/fastapi/discussions/10252
    model_config = ConfigDict(json_encoders={datetime: lambda x: x.strftime(settings.DATETIME_FORMAT)})

    code: int = CustomResponseCode.HTTP_200.code
    msg: str = CustomResponseCode.HTTP_200.msg
    data: Any | None = None


class ResponseBase:
    """
    Unified response methods

    .. tip::

        The methods in this class will return the ResponseModel model, existing as a coding style;

    E.g. ::

        @router.get('/test')
        def test() -> ResponseModel:
            return response_base.success(data={'test': 'test'})
    """

    @staticmethod
    def __response(*, res: CustomResponseCode | CustomResponse = None, data: Any | None = None) -> ResponseModel:
        """
        General method for successful request response

        :param res: Response information
        :param data: Response data
        :return: ResponseModel
        """
        return ResponseModel(code=res.code, msg=res.msg, data=data)

    def success(
        self,
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_200,
        data: Any | None = None,
    ) -> ResponseModel:
        return self.__response(res=res, data=data)

    def fail(
        self,
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_400,
        data: Any = None,
    ) -> ResponseModel:
        return self.__response(res=res, data=data)

    @staticmethod
    def fast_success(
        *,
        res: CustomResponseCode | CustomResponse = CustomResponseCode.HTTP_200,
        data: Any | None = None,
    ) -> Response:
        """
        This method is created to improve the interface response speed. If the returned data does not need to be parsed and validated by pydantic, it is recommended to use it. Otherwise, please do not use it!

        .. warning::

            When using this return method, do not specify the interface parameter response_model, and do not add an arrow return type after the interface function

        :param res: Response information
        :param data: Response data
        :return: Response
        """
        return MsgSpecJSONResponse({'code': res.code, 'msg': res.msg, 'data': data})


response_base = ResponseBase()