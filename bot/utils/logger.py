"""
Настройка логирования.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "otchebot",
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Настройка логгера.

    Args:
        name: Имя логгера
        level: Уровень логирования
        format_string: Формат сообщений

    Returns:
        logging.Logger: Настроенный логгер
    """
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Если уже есть обработчики, не добавляем новые
    if logger.handlers:
        return logger

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(format_string))

    logger.addHandler(console_handler)

    return logger


# Глобальный логгер
logger = setup_logger()
