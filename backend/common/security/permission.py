#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request

from backend.common.exception.errors import ServerError
from backend.core.conf import settings


class RequestPermission:
    """
    Request permission, only used for role-menu RBAC

    Tip:
        When using this request permission, you need to set `Depends(RequestPermission('xxx'))` before `DependsRBAC`,
        because the current version of FastAPI executes interface dependency injection in order, which means the RBAC
        identifier will be set before validation.
    """

    def __init__(self, value: str):
        self.value = value

    async def __call__(self, request: Request):
        if settings.PERMISSION_MODE == 'role-menu':
            if not isinstance(self.value, str):
                raise ServerError
            # Attach permission identifier
            request.state.permission = self.value