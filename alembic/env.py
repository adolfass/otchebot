# Alembic Script Configuration
"""
Конфигурация Alembic для асинхронных миграций PostgreSQL.
"""

from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импорт моделей для автогенерации миграций
from bot.database.models import Base, Complaint  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """
    Получение URL базы данных из переменных окружения.
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://otchebot_user:password@localhost:5432/otchebot"
    )
    return database_url


def run_migrations_offline() -> None:
    """
    Запуск миграций в 'офлайн' режиме.

    Без подключения к базе данных.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в 'онлайн' режиме.

    С подключением к базе данных.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def run_async_migrations(connection: Connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    async def run_async():
        async with connectable.connect() as connection:
            await connection.run_sync(run_async_migrations)

    import asyncio
    asyncio.run(run_async())

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
