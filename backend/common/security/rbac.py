#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import casbin
import casbin_async_sqlalchemy_adapter
from fastapi import Depends, Request

from backend.app.admin.model import CasbinRule
from backend.common.enums import MethodType, StatusType
from backend.common.exception.errors import AuthorizationError, TokenError
from backend.common.security.jwt import DependsJwtAuth
from backend.core.conf import settings
from backend.database.db_mysql import async_engine


class RBAC:
    @staticmethod
    async def enforcer() -> casbin.AsyncEnforcer:
        """
        Get the casbin enforcer

        :return: casbin.AsyncEnforcer
        """
        # Define the rule data directly within the method
        _CASBIN_RBAC_MODEL_CONF_TEXT = """
        [request_definition]
        r = sub, obj, act

        [policy_definition]
        p = sub, obj, act

        [role_definition]
        g = _, _

        [policy_effect]
        e = some(where (p.eft == allow))

        [matchers]
        m = g(r.sub, p.sub) && (keyMatch(r.obj, p.obj) || keyMatch3(r.obj, p.obj)) && (r.act == p.act || p.act == "*")
        """
        adapter = casbin_async_sqlalchemy_adapter.Adapter(async_engine, db_class=CasbinRule)
        model = casbin.AsyncEnforcer.new_model(text=_CASBIN_RBAC_MODEL_CONF_TEXT)
        enforcer = casbin.AsyncEnforcer(model, adapter)
        await enforcer.load_policy()
        return enforcer

    async def rbac_verify(self, request: Request, _token: str = DependsJwtAuth) -> None:
        """
        RBAC permission verification

        :param request: The request object
        :param _token: The JWT token
        :return: None
        """
        path = request.url.path
        # Authorization whitelist
        if path in settings.TOKEN_REQUEST_PATH_EXCLUDE:
            return
        # Force JWT authorization status check
        if not request.auth.scopes:
            raise TokenError
        # Superuser exemption from verification
        if request.user.is_superuser:
            return
        # Check role data permission scope
        user_roles = request.user.roles
        if not user_roles:
            raise AuthorizationError(msg='User has not been assigned a role, authorization failed')
        if not any(len(role.menus) > 0 for role in user_roles):
            raise AuthorizationError(msg='User\'s roles have not been assigned menus, authorization failed')
        method = request.method
        if method != MethodType.GET or method != MethodType.OPTIONS:
            if not request.user.is_staff:
                raise AuthorizationError(msg='This user is prohibited from backend management operations')
        # Data permission scope
        data_scope = any(role.data_scope == 1 for role in user_roles)
        if data_scope:
            return
        user_uuid = request.user.uuid
        if settings.PERMISSION_MODE == 'role-menu':
            # Role menu permission verification
            path_auth_perm = getattr(request.state, 'permission', None)
            # No menu permission identifier, no verification
            if not path_auth_perm:
                return
            if path_auth_perm in set(settings.RBAC_ROLE_MENU_EXCLUDE):
                return
            allow_perms = []
            for role in user_roles:
                for menu in role.menus:
                    if menu.status == StatusType.enable:
                        allow_perms.extend(menu.perms.split(','))
            if path_auth_perm not in allow_perms:
                raise AuthorizationError
        else:
            # Casbin permission verification
            if (method, path) in settings.RBAC_CASBIN_EXCLUDE:
                return
            enforcer = await self.enforcer()
            if not enforcer.enforce(user_uuid, path, method):
                raise AuthorizationError


rbac = RBAC()
# RBAC authorization dependency injection
DependsRBAC = Depends(rbac.rbac_verify)
