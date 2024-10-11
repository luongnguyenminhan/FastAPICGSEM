#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import timedelta

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.common.dataclasses import AccessToken, NewToken, RefreshToken
from backend.common.exception.errors import AuthorizationError, TokenError
from backend.core.conf import settings
from backend.database.db_redis import redis_client
from backend.utils.timezone import timezone

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# JWT authorizes dependency injection
DependsJwtAuth = Depends(HTTPBearer())


def get_hash_password(password: str) -> str:
    """
    Encrypt passwords using the hash algorithm

    :param password: The password to encrypt
    :return: The hashed password
    """
    return pwd_context.hash(password)


def password_verify(plain_password: str, hashed_password: str) -> bool:
    """
    Password verification

    :param plain_password: The password to verify
    :param hashed_password: The hash ciphers to compare
    :return: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


async def create_access_token(sub: str, multi_login: bool) -> AccessToken:
    """
    Generate encryption token

    :param sub: The subject/userid of the JWT
    :param multi_login: Multipoint login for user
    :return: AccessToken object containing the token and its expiration time
    """
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_EXPIRE_SECONDS)
    expire_seconds = settings.TOKEN_EXPIRE_SECONDS

    to_encode = {'exp': expire, 'sub': sub}
    access_token = jwt.encode(to_encode, settings.TOKEN_SECRET_KEY, settings.TOKEN_ALGORITHM)

    if not multi_login:
        key_prefix = f'{settings.TOKEN_REDIS_PREFIX}:{sub}'
        await redis_client.delete_prefix(key_prefix)

    key = f'{settings.TOKEN_REDIS_PREFIX}:{sub}:{access_token}'
    await redis_client.setex(key, expire_seconds, access_token)
    return AccessToken(access_token=access_token, access_token_expire_time=expire)


async def create_refresh_token(sub: str, multi_login: bool) -> RefreshToken:
    """
    Generate encryption refresh token, only used to create a new token

    :param sub: The subject/userid of the JWT
    :param multi_login: Multipoint login for user
    :return: RefreshToken object containing the token and its expiration time
    """
    expire = timezone.now() + timedelta(seconds=settings.TOKEN_REFRESH_EXPIRE_SECONDS)
    expire_seconds = settings.TOKEN_REFRESH_EXPIRE_SECONDS

    to_encode = {'exp': expire, 'sub': sub}
    refresh_token = jwt.encode(to_encode, settings.TOKEN_SECRET_KEY, settings.TOKEN_ALGORITHM)

    if not multi_login:
        key_prefix = f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{sub}'
        await redis_client.delete_prefix(key_prefix)

    key = f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{sub}:{refresh_token}'
    await redis_client.setex(key, expire_seconds, refresh_token)
    return RefreshToken(refresh_token=refresh_token, refresh_token_expire_time=expire)


async def create_new_token(sub: str, token: str, refresh_token: str, multi_login: bool) -> NewToken:
    """
    Generate new token

    :param sub: The subject/userid of the JWT
    :param token: The current token
    :param refresh_token: The current refresh token
    :param multi_login: Multipoint login for user
    :return: NewToken object containing the new tokens and their expiration times
    """
    redis_refresh_token = await redis_client.get(f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{sub}:{refresh_token}')
    if not redis_refresh_token or redis_refresh_token != refresh_token:
        raise TokenError(msg='Refresh Token has expired')

    new_access_token = await create_access_token(sub, multi_login)
    new_refresh_token = await create_refresh_token(sub, multi_login)

    token_key = f'{settings.TOKEN_REDIS_PREFIX}:{sub}:{token}'
    refresh_token_key = f'{settings.TOKEN_REFRESH_REDIS_PREFIX}:{sub}:{refresh_token}'
    await redis_client.delete(token_key)
    await redis_client.delete(refresh_token_key)
    return NewToken(
        new_access_token=new_access_token.access_token,
        new_access_token_expire_time=new_access_token.access_token_expire_time,
        new_refresh_token=new_refresh_token.refresh_token,
        new_refresh_token_expire_time=new_refresh_token.refresh_token_expire_time,
    )


def get_token(request: Request) -> str:
    """
    Get token from request header

    :param request: The request object
    :return: The token string
    """
    authorization = request.headers.get('Authorization')
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != 'bearer':
        raise TokenError(msg='Invalid token')
    return token


def jwt_decode(token: str) -> int:
    """
    Decode token

    :param token: The token to decode
    :return: The user ID
    """
    try:
        payload = jwt.decode(token, settings.TOKEN_SECRET_KEY, algorithms=[settings.TOKEN_ALGORITHM])
        user_id = int(payload.get('sub'))
        if not user_id:
            raise TokenError(msg='Invalid token')
    except ExpiredSignatureError:
        raise TokenError(msg='Token has expired')
    except (JWTError, Exception):
        raise TokenError(msg='Invalid token')
    return user_id


async def jwt_authentication(token: str) -> int:
    """
    JWT authentication

    :param token: The token to authenticate
    :return: The user ID
    """
    user_id = jwt_decode(token)
    key = f'{settings.TOKEN_REDIS_PREFIX}:{user_id}:{token}'
    token_verify = await redis_client.get(key)
    if not token_verify:
        raise TokenError(msg='Token has expired')
    return user_id


async def get_current_user(db: AsyncSession, pk: int) -> User:
    """
    Get the current user through token

    :param db: The database session
    :param pk: The user ID
    :return: The User object
    """
    from backend.app.admin.crud.crud_user import user_dao

    user = await user_dao.get_with_relation(db, user_id=pk)
    if not user:
        raise TokenError(msg='Invalid token')
    if not user.status:
        raise AuthorizationError(msg='User has been locked, please contact the system administrator')
    if user.dept_id:
        if not user.dept.status:
            raise AuthorizationError(msg='User\'s department has been locked')
        if user.dept.del_flag:
            raise AuthorizationError(msg='User\'s department has been deleted')
    if user.roles:
        role_status = [role.status for role in user.roles]
        if all(status == 0 for status in role_status):
            raise AuthorizationError(msg='User\'s roles have been locked')
    return user


def superuser_verify(request: Request) -> bool:
    """
    Verify the current user permissions through token

    :param request: The request object
    :return: True if the user is a superuser, False otherwise
    """
    superuser = request.user.is_superuser
    if not superuser or not request.user.is_staff:
        raise AuthorizationError
    return superuser
