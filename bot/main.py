"""
Главный файл запуска Telegram бота.
"""

import asyncio
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command

from bot.config import settings
from bot.database.crud import Database
from bot.services.form import FormService, AntiFloodService
from bot.services.user_data import UserDataCollector
from bot.services.scheduler import DailyReportScheduler
from bot.handlers.common import router, init_handlers
from bot.handlers.group import router as group_router, init_group_handlers
from bot.handlers.admin import router as admin_router
from bot.handlers.context import set_channel_id
from bot.utils.logger import logger


# Глобальные объекты
bot: Bot = None
dp: Dispatcher = None
db: Database = None
scheduler: DailyReportScheduler = None


async def cmd_test_report(message, state):
    """Тестовая команда для отправки отчёта."""
    global scheduler
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ Доступ запрещён.")
        return
    
    if scheduler:
        await scheduler.send_test_report(message.from_user.id)
        await message.answer("✅ Тестовый отчёт отправлен!")
    else:
        await message.answer("❌ Планировщик не инициализирован.")


async def on_startup():
    """Действия при запуске бота."""
    global scheduler
    
    logger.info("Бот запускается...")

    # Создание таблиц БД
    await db.create_tables()
    logger.info("Таблицы БД созданы/проверены")

    # Информация о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот запущен: @{bot_info.username} (ID: {bot_info.id})")
    
    # Запуск планировщика отчётов
    scheduler = DailyReportScheduler(bot, db, report_hour=11, report_minute=0)
    await scheduler.start()
    logger.info("Планировщик отчётов запущен")


async def on_shutdown():
    """Действия при остановке бота."""
    global scheduler
    
    logger.info("Бот останавливается...")

    # Остановка планировщика
    if scheduler:
        await scheduler.stop()
    
    # Закрытие соединений
    await db.close()
    await bot.session.close()

    logger.info("Бот остановлен")


async def main():
    """Основная функция запуска."""
    global bot, dp, db

    # Инициализация компонентов
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(group_router)
    dp.include_router(admin_router)

    db = Database(settings.DATABASE_URL)

    # Инициализация сервисов
    antiflood_service = AntiFloodService(interval_seconds=settings.ANTIFLOOD_INTERVAL)
    form_service = FormService(antiflood_service)
    user_data_collector = UserDataCollector(bot)

    # Инициализация хендлеров
    init_handlers(db, form_service, user_data_collector)
    init_group_handlers(db)
    
    # Регистрация дополнительных команд
    dp.message.register(cmd_test_report, Command(commands=["test_report"]))

    # Регистрация хендлеров запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск polling
    logger.info("Запуск polling...")
    await dp.start_polling(bot)


def signal_handler(sig, frame):
    """Обработчик сигналов завершения."""
    logger.info(f"Получен сигнал {sig}, завершение работы...")
    asyncio.create_task(on_shutdown())
    sys.exit(0)


if __name__ == "__main__":
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка бота (KeyboardInterrupt)")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)
