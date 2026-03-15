"""
Валидаторы данных.
"""

import re
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

    # Проверка на минимальную длину
    if len(text.strip()) < 10:
        return False, "Текст слишком короткий. Пожалуйста, опишите вашу проблему подробнее."

    # Проверка на нечитаемый текст
    is_readable, reason = check_readable_text(text)
    if not is_readable:
        return False, f"Текст нечитаемый: {reason}"

    return True, None


def check_readable_text(text: str) -> Tuple[bool, Optional[str]]:
    """
    Проверка текста на читаемость.

    Args:
        text: Текст для проверки

    Returns:
        Tuple[bool, Optional[str]]: (читаемый, причина если нет)
    """
    # Убираем пробелы для анализа
    text_no_space = text.replace(" ", "")
    
    # Проверка: есть ли буквы (русские или английские)
    has_letters = bool(re.search(r'[а-яёa-zA-Z]', text_no_space))
    if not has_letters:
        return False, "текст должен содержать буквы"
    
    # Проверка: слишком много спецсимволов подряд
    if re.search(r'[!@#$%^&*()_+=\[\]{}|\\:;"<>,\./]{10,}', text_no_space):
        return False, "слишком много спецсимволов"
    
    # Проверка: только цифры
    if text_no_space.isdigit():
        return False, "текст не может состоять только из цифр"
    
    # Проверка: слишком много заглавных букв подряд (Caps Lock)
    caps_count = len(re.findall(r'[A-ZА-ЯЁ]{5,}', text_no_space))
    if caps_count > 3:
        return False, "слишком много ЗАГЛАВНЫХ букв"
    
    # Проверка: есть ли хоть какое-то осмысленное слово (минимум 3 символа)
    words = re.findall(r'[а-яёa-zA-Z]{3,}', text.lower())
    if len(words) < 2:
        return False, "текст должен содержать хотя бы 2 слова"
    
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
    text = re.sub(r"\s+", " ", text)

    return text
