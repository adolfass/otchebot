"""
Валидаторы данных.
"""

from typing import Optional, Tuple


def validate_confession_text(text: str, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Валидация текста исповеди.

    Args:
        text: Текст для валидации
        max_length: Максимальная длина текста

    Returns:
        Tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
    """
    if not text or not text.strip():
        return False, "Текст не может быть пустым."

    if len(text) > max_length:
        return (
            False,
            f"Текст слишком длинный (максимум {max_length} символов). "
            f"Сейчас: {len(text)} символов.",
        )

    return True, None


def validate_user_id(user_id: int) -> bool:
    """
    Валидация Telegram user ID.

    Args:
        user_id: ID пользователя

    Returns:
        bool: True если ID валиден
    """
    return isinstance(user_id, int) and user_id > 0


def sanitize_text(text: str) -> str:
    """
    Очистка текста от лишних пробелов и символов.

    Args:
        text: Исходный текст

    Returns:
        str: Очищенный текст
    """
    # Удаляем ведущие и замыкающие пробелы
    text = text.strip()

    # Заменяем множественные пробелы на один
    import re
    text = re.sub(r"\s+", " ", text)

    return text
