"""
Сервис ежедневных уведомлений для администратора.
"""

import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

from bot.config import settings
from bot.database.crud import Database, MemberEventCRUD, ComplaintCRUD
from bot.database.models import MemberEventType, ComplaintStatus
from bot.utils.logger import logger


class DailyReportScheduler:
    """Планировщик ежедневных отчётов."""

    def __init__(self, bot: Bot, db: Database, report_hour: int = 11, report_minute: int = 0):
        self.bot = bot
        self.db = db
        self.report_hour = report_hour
        self.report_minute = report_minute
        self._task = None
        self._running = False

    async def start(self):
        """Запуск планировщика."""
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Планировщик отчётов запущен (время: {self.report_hour:02d}:{self.report_minute:02d})")

    async def stop(self):
        """Остановка планировщика."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик отчётов остановлен")

    async def _run_scheduler(self):
        """Основной цикл планировщика."""
        while self._running:
            try:
                now = datetime.now()
                
                next_run = now.replace(hour=self.report_hour, minute=self.report_minute, second=0, microsecond=0)
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                seconds_until_next = (next_run - now).total_seconds()
                logger.info(f"Следующий отчёт через {seconds_until_next/3600:.1f} часов")
                
                await asyncio.sleep(seconds_until_next)
                
                if self._running:
                    await self._send_daily_report()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)

    async def _send_daily_report(self):
        """Отправка ежедневного отчёта администратору."""
        from datetime import timedelta
        from sqlalchemy import select, func
        
        now = datetime.now()
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        async with self.db.async_session_factory() as session:
            member_crud = MemberEventCRUD(session)
            complaint_crud = ComplaintCRUD(session)
            
            joined_count = await member_crud.get_count_since(
                MemberEventType.JOINED, since
            )
            left_count = await member_crud.get_count_since(
                MemberEventType.LEFT, since
            )
            
            from bot.database.models import Complaint
            result = await session.execute(
                select(func.count()).select_from(Complaint).where(
                    Complaint.status == ComplaintStatus.NEW,
                    Complaint.created_at >= since
                )
            )
            new_complaints = result.scalar() or 0
        
        report_text = (
            "📊 **Ежедневный отчёт**\n\n"
            f"👥 *Новые участники:* {joined_count}\n"
            f"🚪 *Покинули группу:* {left_count}\n"
            f"📝 *Новые исповеди:* {new_complaints}\n\n"
            f"_{now.strftime('%Y-%m-%d %H:%M')}_"
        )
        
        for admin_id in settings.admin_ids_list:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=report_text,
                    parse_mode="Markdown"
                )
                logger.info(f"Отчёт отправлен админу {admin_id}")
            except Exception as e:
                logger.error(f"Не удалось отправить отчёт админу {admin_id}: {e}")

    async def send_test_report(self, admin_id: int):
        """Отправка тестового отчёта (для проверки)."""
        await self._send_daily_report()
