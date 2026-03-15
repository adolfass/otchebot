"""
FastAPI сервер для OTCHÉBOT API.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api.routes import router as problems_router
from api.dependencies import get_db_session
from bot.database.crud import Database
from bot.config import settings
from bot.utils.logger import logger


# Глобальный объект БД
db: Database = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Управление жизненным циклом приложения."""
    global db

    # Startup
    logger.info("API Server запускается...")
    db = Database(settings.DATABASE_URL)
    await db.create_tables()
    logger.info("Таблицы БД созданы/проверены")

    yield

    # Shutdown
    logger.info("API Server останавливается...")
    await db.close()
    logger.info("API Server остановлен")


app = FastAPI(
    title="OTCHÉBOT API",
    description="API для получения заявок (исповедей) пользователей IT-сферы",
    version="1.0.0",
    lifespan=lifespan,
)

# Подключение роутов
app.include_router(problems_router, prefix="/api/v1", tags=["Problems"])


@app.get("/health")
async def health_check():
    """Проверка здоровья API."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "OTCHÉBOT API",
        "docs": "/docs",
        "health": "/health",
    }
