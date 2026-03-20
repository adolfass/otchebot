# AGENTS.md - OTCHEBOT Development Guide

This file contains instructions for agentic coding agents working on this repository.

## Project Overview

OTCHEBOT is a Telegram bot for collecting "confessions" - free-text descriptions of IT problems from users. It consists of:
- **Bot**: aiogram 3.x Telegram bot with FSM for confession collection
- **API Server**: FastAPI server for external agents to pull data
- **Database**: PostgreSQL with async SQLAlchemy

## Build/Lint/Test Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Telegram bot
python -m bot.main

# Run the API server
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
# Build and start all services
docker-compose up --build

# Start specific service
docker-compose up bot
docker-compose up api

# View logs
docker-compose logs -f bot
docker-compose logs -f api
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run a single test file
pytest tests/test_api.py

# Run a single test function
pytest tests/test_api.py::test_get_problems

# Run tests matching a pattern
pytest -k "test_get"

# Run with verbose output
pytest -v

# Run async tests
pytest tests/ --asyncio-mode=auto
```

### Code Quality

```bash
# Format code (Black)
black .

# Sort imports (isort)
isort .

# Lint code (flake8)
flake8 .

# Type checking (mypy)
mypy .

# All checks (if Makefile exists)
make lint
make format
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Code Style Guidelines

### General Principles

1. **All code must be async** - Use `async def` for all functions that perform I/O
2. **No secrets in code** - All secrets go in `.env`, access via `settings`
3. **Type hints required** - Always use type annotations for function signatures
4. **Docstrings in Russian** - Document functions with Russian explanations

### Python Version

- Minimum: Python 3.10+
- Use `from __future__ import annotations` for forward references if needed

### Imports Organization

```python
# 1. Standard library
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Tuple

# 2. Third-party packages (aiogram, fastapi, sqlalchemy, etc.)
from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local imports (relative)
from bot.config import settings
from bot.database.crud import Database
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `user_data.py` |
| Classes | PascalCase | `FormService`, `ComplaintCRUD` |
| Functions | snake_case | `get_user_data`, `validate_confession_text` |
| Variables | snake_case | `user_id`, `complaint_list` |
| Constants | UPPER_SNAKE | `MAX_TEXT_LENGTH`, `ADMIN_IDS` |
| Enum values | UPPER_SNAKE | `ComplaintStatus.NEW` |

### Type Annotations

```python
# Good
async def get_user_data(user_id: int) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    ...

# Good with modern Python
def process_complaint(complaint: Complaint) -> bool:
    ...
```

### Function Structure

```python
async def process_confession_text(message: Message, state: FSMContext) -> None:
    """Обработка текста исповеди."""
    user_id = message.from_user.id
    text = sanitize_text(message.text)

    # Валидация
    is_valid, error_msg = validate_confession_text(text, FormService.MAX_TEXT_LENGTH)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nПопробуйте ещё раз.")
        return

    # Основная логика
    await state.update_data(confession_text=text)
    await state.set_state(ConfessionStates.waiting_consent)

    logger.info(f"User {user_id} submitted confession text")
```

### Error Handling

```python
# Always use try/except for external API calls
try:
    user = await self.bot.get_chat(user_id)
except Exception as e:
    logger.warning(f"Failed to get user data: {e}")
    return None, None, None, None

# Use early returns for validation
if user_id not in settings.admin_ids_list:
    await message.answer("❌ Доступ запрещён.")
    logger.warning(f"Unauthorized admin access attempt from user {user_id}")
    return

# Raise HTTPException for API errors
raise HTTPException(
    status_code=404,
    detail=f"Заявка с ID {problem_id} не найдена",
)
```

### SQLAlchemy Patterns

```python
# Async session usage
async with db.async_session_factory() as session:
    crud = ComplaintCRUD(session)
    complaint = await crud.create(
        user_id=user_id,
        text=text,
        username=username,
    )

# Query pattern
result = await self.session.execute(
    select(Complaint)
    .where(Complaint.status == ComplaintStatus.NEW)
    .order_by(Complaint.created_at.asc())
    .limit(limit)
    .offset(offset)
)
complaints = result.scalars().all()
```

### Pydantic Models for API

```python
class ProblemResponse(BaseModel):
    """Модель ответа с данными заявки."""

    id: int
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    text: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
```

### FastAPI Dependencies

```python
async def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """Проверка API ключа."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API ключ не предоставлен",
        )
    if api_key != settings.EXTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный API ключ",
        )
    return api_key
```

### Logging Patterns

```python
from bot.utils.logger import logger

# Log user actions (only IDs, no personal data)
logger.info(f"User {user_id} started confession process")

# Log errors with context
logger.warning(f"Failed to get user data: {e}")

# Log critical errors with exception
logger.exception(f"Critical error: {e}")
```

### aiogram Handler Patterns

```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.clear()
    # ...

@router.callback_query(F.data == "consent_yes")
async def process_consent_yes(callback: CallbackQuery, state: FSMContext):
    """Обработка согласия."""
    await callback.answer()
    # ...
```

## Project Structure

```
/project/otchebot/
├── bot/                    # Telegram bot application
│   ├── main.py            # Entry point
│   ├── config.py          # Settings (pydantic)
│   ├── database/          # DB models and CRUD
│   │   ├── models.py      # SQLAlchemy models
│   │   └── crud.py        # Database operations
│   ├── handlers/          # Message/command handlers
│   │   ├── common.py      # User handlers
│   │   └── group.py       # Group handlers
│   ├── services/          # Business logic
│   │   ├── form.py        # FSM and validation
│   │   └── user_data.py   # User profile collection
│   └── utils/             # Utilities
│       ├── logger.py      # Logging setup
│       └── validators.py  # Input validation
├── api/                    # FastAPI server
│   ├── server.py          # App entry point
│   ├── routes.py          # API endpoints
│   └── dependencies.py    # Auth, DB session
├── tests/                  # Test suite (add tests here)
├── alembic/               # Database migrations
├── scripts/               # DevOps scripts
├── docker-compose.yml     # Container orchestration
├── Dockerfile.bot         # Bot container
├── Dockerfile.api         # API container
└── requirements.txt       # Python dependencies
```

## Environment Variables

All configuration via `.env` (see `.env.example`):

```env
BOT_TOKEN=...              # Telegram bot token
ADMIN_IDS=123456,789012    # Comma-separated admin IDs
DATABASE_URL=postgresql+asyncpg://...
EXTERNAL_API_KEY=...       # For API authentication
LOG_LEVEL=INFO
ANTIFLOOD_INTERVAL=60      # Seconds between requests
```

## Security Requirements

1. Never commit `.env` - it's in `.gitignore`
2. Validate all user input before processing
3. Log only IDs, not personal data
4. Use parameterized queries (SQLAlchemy ORM)
5. API endpoints require `X-API-Key` header

## Testing Requirements

- Tests go in `tests/` directory
- Use `pytest` with `pytest-asyncio` for async tests
- Mock Telegram API calls when testing handlers
- Test database operations with test DB or mocks
- Target: 70%+ code coverage
