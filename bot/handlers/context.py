"""
Общий контекст для хендлеров.
"""

CHANNEL_ID: int | None = None


def set_channel_id(chat_id: int):
    """Установка ID канала."""
    global CHANNEL_ID
    CHANNEL_ID = chat_id
