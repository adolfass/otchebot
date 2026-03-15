"""
Сервис управления формой сбора исповеди.
FSM (Finite State Machine) и валидация данных.
"""

from datetime import datetime
from typing import Dict, Optional

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class ConfessionStates(StatesGroup):
    """Состояния FSM для сбора исповеди."""

    waiting_text = State()  # Ожидание текста исповеди
    waiting_consent = State()  # Ожидание согласия на сбор данных


class AntiFloodService:
    """
    Сервис антифлуда.
    In-memory словарь для отслеживания последних запросов.
    """

    def __init__(self, interval_seconds: int = 60):
        self._requests: Dict[int, datetime] = {}
        self._interval = interval_seconds

    def can_proceed(self, user_id: int) -> bool:
        """
        Проверка, может ли пользователь сделать запрос.

        Args:
            user_id: Telegram ID пользователя

        Returns:
            bool: True если запрос разрешён
        """
        now = datetime.utcnow()
        last_request = self._requests.get(user_id)

        if last_request is None:
            self._requests[user_id] = now
            return True

        elapsed = (now - last_request).total_seconds()
        if elapsed >= self._interval:
            self._requests[user_id] = now
            return True

        return False

    def get_wait_time(self, user_id: int) -> int:
        """
        Получение времени ожидания для пользователя.

        Args:
            user_id: Telegram ID пользователя

        Returns:
            int: Время ожидания в секундах
        """
        last_request = self._requests.get(user_id)
        if last_request is None:
            return 0

        elapsed = (datetime.utcnow() - last_request).total_seconds()
        return max(0, int(self._interval - elapsed))

    def reset(self, user_id: int):
        """Сброс записи для пользователя (при перезапуске бота)."""
        if user_id in self._requests:
            del self._requests[user_id]

    def clear(self):
        """Очистка всех записей (при перезапуске бота)."""
        self._requests.clear()


class FormService:
    """
    Сервис управления формой сбора исповеди.
    """

    MAX_TEXT_LENGTH = 500
    MIN_TEXT_LENGTH = 1

    def __init__(self, antiflood_service: AntiFloodService):
        self.antiflood = antiflood_service

    def validate_text(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Валидация текста исповеди.

        Args:
            text: Текст для валидации

        Returns:
            tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        if not text or not text.strip():
            return False, "Пожалуйста, введите текст (не пустой)."

        if len(text) > self.MAX_TEXT_LENGTH:
            return (
                False,
                f"Текст слишком длинный (максимум {self.MAX_TEXT_LENGTH} символов). "
                f"Сейчас: {len(text)} символов.",
            )

        return True, None

    async def start_confession(
        self, user_id: int, state: FSMContext
    ) -> tuple[bool, Optional[str]]:
        """
        Начало процесса сбора исповеди.

        Args:
            user_id: Telegram ID пользователя
            state: FSM context

        Returns:
            tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        # Проверка антифлуда
        if not self.antiflood.can_proceed(user_id):
            wait_time = self.antiflood.get_wait_time(user_id)
            return (
                False,
                f"Пожалуйста, подождите {wait_time} сек. перед новой заявкой.",
            )

        # Установка состояния ожидания текста
        await state.update_data(confession_start=datetime.utcnow())
        return True, None
