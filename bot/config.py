"""
Конфигурация приложения.
Загрузка переменных окружения и настройка параметров.
"""

import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения."""

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота")

    # Admin IDs
    ADMIN_IDS: str = Field(..., description="Список ID администраторов через запятую")

    @property
    def admin_ids_list(self) -> List[int]:
        """Преобразует строку ADMIN_IDS в список целых чисел."""
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    # Database
    DATABASE_URL: str = Field(
        ...,
        description="URL подключения к PostgreSQL",
    )

    # External API
    EXTERNAL_API_KEY: str = Field(
        ...,
        description="API ключ для внешнего агента",
    )

    # Backup Server
    BACKUP_SERVER: str = Field(
        default="",
        description="IP адрес сервера для бэкапов",
    )
    BACKUP_SSH_KEY: str = Field(
        default="",
        description="Путь к SSH ключу для бэкапов",
    )
    BACKUP_PATH: str = Field(
        default="",
        description="Путь для хранения бэкапов",
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Уровень логирования",
    )

    # Anti-flood
    ANTIFLOOD_INTERVAL: int = Field(
        default=60,
        description="Интервал антифлуда в секундах",
    )

    # Application
    APP_NAME: str = "OTCHEBOT"
    VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Глобальный экземпляр настроек
settings = Settings()
