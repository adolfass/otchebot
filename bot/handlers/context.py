"""
Общий контекст для хендлеров.
"""

from bot.config import settings


CHANNEL_ID: int | None = None


def set_channel_id(chat_id: int):
    """Установка ID канала."""
    global CHANNEL_ID
    CHANNEL_ID = chat_id


def get_channel_id() -> int | None:
    """Получение ID канала (из памяти или из настроек)."""
    global CHANNEL_ID
    if CHANNEL_ID is not None:
        return CHANNEL_ID
    if settings.CHANNEL_ID != 0:
        return settings.CHANNEL_ID
    return None
