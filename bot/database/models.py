"""
Модели базы данных.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, BigInteger, Text, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class ComplaintStatus(enum.Enum):
    """Статусы заявки."""

    NEW = "new"  # Новая заявка
    SENT = "sent"  # Отправлена внешнему агенту
    PROCESSED = "processed"  # Обработана администратором


class MemberEventType(enum.Enum):
    """Типы событий с участниками."""

    JOINED = "joined"
    LEFT = "left"


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


class Complaint(Base):
    """
    Модель заявки (исповеди) пользователя.

    Атрибуты:
        id: Уникальный идентификатор заявки
        user_id: Telegram ID пользователя
        username: Username пользователя (если есть)
        first_name: Имя пользователя
        last_name: Фамилия пользователя (если есть)
        photo_file_id: File ID самого большого фото профиля (если есть)
        text: Текст заявки (до 500 символов)
        status: Статус заявки (new, sent, processed)
        created_at: Дата и время создания заявки
        updated_at: Дата и время последнего обновления
    """

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus, name="complaint_status", create_type=True),
        default=ComplaintStatus.NEW,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Complaint(id={self.id}, user_id={self.user_id}, status={self.status.value})>"


class MemberEvent(Base):
    """
    Модель событий с участниками группы.

    Атрибуты:
        id: Уникальный идентификатор
        user_id: Telegram ID пользователя
        username: Username пользователя
        first_name: Имя пользователя
        event_type: Тип события (joined/left)
        chat_id: ID чата/канала
        created_at: Дата и время события
    """

    __tablename__ = "member_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_type: Mapped[MemberEventType] = mapped_column(
        SQLEnum(MemberEventType, name="member_event_type", create_type=True),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<MemberEvent(id={self.id}, user_id={self.user_id}, event_type={self.event_type.value})>"
