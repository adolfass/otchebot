"""
CRUD операции для работы с заявками.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from bot.database.models import Complaint, ComplaintStatus, MemberEvent, MemberEventType


class Database:
    """Управление подключением к базе данных."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            self.database_url,
            poolclass=NullPool,
            echo=False,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def create_tables(self):
        """Создание всех таблиц."""
        from bot.database.models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Удаление всех таблиц (для тестов)."""
        from bot.database.models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        """Закрытие соединения с БД."""
        await self.engine.dispose()


class ComplaintCRUD:
    """CRUD операции для заявок."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        text: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_file_id: Optional[str] = None,
    ) -> Complaint:
        """Создание новой заявки."""
        complaint = Complaint(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_file_id=photo_file_id,
            text=text,
            status=ComplaintStatus.NEW,
        )
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: int) -> Optional[Complaint]:
        """Получение заявки по ID."""
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def get_new(
        self, limit: int = 100, offset: int = 0
    ) -> Tuple[List[Complaint], int]:
        """
        Получение новых заявок с пагинацией.

        Returns:
            Tuple[List[Complaint], int]: Список заявок и общее количество
        """
        # Получаем общее количество
        count_result = await self.session.execute(
            select(func.count()).where(Complaint.status == ComplaintStatus.NEW)
        )
        total = count_result.scalar() or 0

        # Получаем заявки
        result = await self.session.execute(
            select(Complaint)
            .where(Complaint.status == ComplaintStatus.NEW)
            .order_by(Complaint.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        complaints = result.scalars().all()
        return list(complaints), total

    async def get_by_user_id(self, user_id: int) -> List[Complaint]:
        """Получение всех заявок пользователя."""
        result = await self.session.execute(
            select(Complaint).where(Complaint.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_status(
        self, complaint_id: int, status: ComplaintStatus
    ) -> Optional[Complaint]:
        """Обновление статуса заявки."""
        complaint = await self.get_by_id(complaint_id)
        if complaint:
            complaint.status = status
            complaint.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(complaint)
        return complaint

    async def mark_as_sent(self, complaint_id: int) -> Optional[Complaint]:
        """Пометка заявки как отправленной."""
        return await self.update_status(complaint_id, ComplaintStatus.SENT)

    async def mark_as_processed(self, complaint_id: int) -> Optional[Complaint]:
        """Пометка заявки как обработанной."""
        return await self.update_status(complaint_id, ComplaintStatus.PROCESSED)

    async def delete_by_user_id(self, user_id: int) -> int:
        """
        Удаление всех заявок пользователя.

        Returns:
            int: Количество удалённых заявок
        """
        result = await self.session.execute(
            delete(Complaint).where(Complaint.user_id == user_id)
        )
        await self.session.commit()
        return result.rowcount or 0

    async def get_statistics(
        self, days: int = 7
    ) -> dict:
        """
        Получение статистики за период.

        Args:
            days: Количество дней для статистики

        Returns:
            dict: Статистика по статусам
        """
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(Complaint.status, func.count())
            .where(Complaint.created_at >= since)
            .group_by(Complaint.status)
        )
        stats = {status.value: count for status, count in result.all()}

        # Общее количество
        total_result = await self.session.execute(
            select(func.count()).where(Complaint.created_at >= since)
        )
        stats["total"] = total_result.scalar() or 0

        return stats


class MemberEventCRUD:
    """CRUD операции для событий участников."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        event_type: MemberEventType,
        chat_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
    ) -> MemberEvent:
        """Создание нового события участника."""
        event = MemberEvent(
            user_id=user_id,
            username=username,
            first_name=first_name,
            event_type=event_type,
            chat_id=chat_id,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_count_since(
        self, event_type: MemberEventType, since: datetime, chat_id: Optional[int] = None
    ) -> int:
        """Получение количества событий с момента."""
        query = select(func.count()).where(
            MemberEvent.event_type == event_type,
            MemberEvent.created_at >= since,
        )
        if chat_id:
            query = query.where(MemberEvent.chat_id == chat_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
