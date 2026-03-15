"""
Сервис сбора данных профиля пользователя Telegram.
"""

from typing import Optional, Tuple

from aiogram import Bot
from aiogram.types import User


class UserDataCollector:
    """
    Сервис для сбора данных профиля пользователя через Telegram API.
    """

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_user_data(
        self, user_id: int
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Получение данных пользователя через Telegram API.

        Args:
            user_id: Telegram ID пользователя

        Returns:
            Tuple[username, first_name, last_name, photo_file_id]:
                Данные пользователя (None если недоступно)
        """
        try:
            # Получаем информацию о пользователе
            user = await self.bot.get_chat(user_id)

            username = user.username if hasattr(user, "username") else None
            first_name = user.first_name if hasattr(user, "first_name") else None
            last_name = user.last_name if hasattr(user, "last_name") else None

            # Получаем фото профиля
            photo_file_id = await self._get_profile_photo(user_id)

            return username, first_name, last_name, photo_file_id

        except Exception as e:
            # Если не удалось получить данные, возвращаем None
            return None, None, None, None

    async def _get_profile_photo(self, user_id: int) -> Optional[str]:
        """
        Получение file_id самого большого фото профиля.

        Args:
            user_id: Telegram ID пользователя

        Returns:
            Optional[str]: file_id фото или None
        """
        try:
            # Получаем профильные фото
            photos = await self.bot.get_user_profile_photos(user_id)

            if not photos or photos.total_count == 0:
                return None

            # Берём последнее фото (самое большое)
            # photos.photos[0] - это список фото разных размеров
            # последний элемент - самое большое фото
            largest_photo = photos.photos[0][-1]
            return largest_photo.file_id

        except Exception:
            return None

    async def get_full_name(self, user: User) -> str:
        """
        Получение полного имени пользователя.

        Args:
            user: Объект пользователя

        Returns:
            str: Полное имя
        """
        parts = []
        if user.first_name:
            parts.append(user.first_name)
        if user.last_name:
            parts.append(user.last_name)

        return " ".join(parts) if parts else user.username or f"User #{user.id}"
