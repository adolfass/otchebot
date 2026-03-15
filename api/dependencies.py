"""
Зависимости FastAPI.
Проверка авторизации и получение сессии БД.
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.crud import Database
from api.server import db


# API Key авторизация
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    Проверка API ключа.

    Args:
        api_key: Ключ из заголовка X-API-Key

    Raises:
        HTTPException: Если ключ невалиден или отсутствует
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API ключ не предоставлен",
            headers={"WWW-Authenticate": "X-API-Key"},
        )

    if api_key != settings.EXTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный API ключ",
            headers={"WWW-Authenticate": "X-API-Key"},
        )

    return api_key


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение сессии базы данных.

    Yields:
        AsyncSession: Сессия БД
    """
    async with db.async_session_factory() as session:
        yield session
