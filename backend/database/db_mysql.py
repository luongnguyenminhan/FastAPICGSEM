#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.common.log import log
from backend.common.model import MappedBase
from backend.core.conf import settings


def create_engine_and_session(url: str | URL):
    try:
        # Database engine
        engine = create_async_engine(url, echo=settings.MYSQL_ECHO, future=True, pool_pre_ping=True)
        # log.success('Database connection successful')
    except Exception as e:
        log.error('❌ Database connection failed {}', e)
        sys.exit()
    else:
        db_session = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        return engine, db_session


SQLALCHEMY_DATABASE_URL = (
    f'mysql+asyncmy://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:'
    f'{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}?charset={settings.MYSQL_CHARSET}'
)

async_engine, async_db_session = create_engine_and_session(SQLALCHEMY_DATABASE_URL)


async def get_db() -> AsyncSession:
    """Session generator"""
    session = async_db_session()
    try:
        yield session
    except Exception as se:
        await session.rollback()
        raise se
    finally:
        await session.close()


# Session Annotated
CurrentSession = Annotated[AsyncSession, Depends(get_db)]


async def create_table():
    """Create database tables"""
    async with async_engine.begin() as coon:
        await coon.run_sync(MappedBase.metadata.create_all)


def uuid4_str() -> str:
    """UUID type compatibility solution for the database engine"""
    return str(uuid4())