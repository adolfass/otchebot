# Инструкция для Opencode Agent

**Версия протокола:** 5.2.0
**Приоритет:** КРИТИЧЕСКИЙ
**Дата:** 2026-03-20

---

## 📋 ЗАДАЧА: Создание миграции для member_events

---

## 🐛 ПРОБЛЕМА

**Отчёт показывает 0 покинувших, хотя бот логирует выход.**

**Причина:** Таблица `member_events` **НЕ СУЩЕСТВУЕТ** в БД!

Миграция `001_initial.py` создаёт только таблицу `complaints`.

---

## 🔧 ИСПРАВЛЕНИЯ

### 1. Создать миграцию для member_events

```bash
cd /project/otchebot

# Создать файл миграции
cat > alembic/versions/002_member_events.py << 'EOF'
"""Create member_events table

Revision ID: 002_member_events
Revises: 001_initial
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_member_events'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class MemberEventType(enum.Enum):
    JOINED = "joined"
    LEFT = "left"


def upgrade() -> None:
    # Создание enum типа для событий
    member_event_type = sa.Enum('joined', 'left', name='member_event_type')
    member_event_type.create(op.get_bind())

    # Создание таблицы member_events
    op.create_table(
        'member_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('event_type', sa.Enum('joined', 'left', name='member_event_type'), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание индексов
    op.create_index(op.f('ix_member_events_event_type'), 'member_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_member_events_user_id'), 'member_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_member_events_created_at'), 'member_events', ['created_at'], unique=False)


def downgrade() -> None:
    # Удаление индексов
    op.drop_index(op.f('ix_member_events_created_at'), table_name='member_events')
    op.drop_index(op.f('ix_member_events_user_id'), table_name='member_events')
    op.drop_index(op.f('ix_member_events_event_type'), table_name='member_events')

    # Удаление таблицы
    op.drop_table('member_events')

    # Удаление enum типа
    member_event_type = sa.Enum('joined', 'left', name='member_event_type')
    member_event_type.drop(op.get_bind())
EOF
```

### 2. Применить миграцию

```bash
cd /project/otchebot

# Перезапустить бота с применением миграций
docker-compose restart bot

# Или применить вручную
docker-compose exec bot alembic upgrade head
```

### 3. Проверить

```bash
# Проверить таблицу
docker-compose exec postgres psql -U otchebot_user -d otchebot -c "\dt"

# Ожидается: member_events

# Проверить миграции
docker-compose exec bot alembic current
```

---

## 🧪 ТЕСТЫ

### Тест 1: Таблица создана

```bash
docker-compose exec postgres psql -U otchebot_user -d otchebot -c "SELECT count(*) FROM member_events;"
```

### Тест 2: Выход фиксируется

1. Выйти из группы
2. Проверить логи: `🚪 Участник покинул`
3. Проверить БД: `SELECT * FROM member_events WHERE event_type='left';`

### Тест 3: Отчёт верный

```bash
# Отправить тестовый отчёт
/test_report
```

**Ожидается:** Правильное количество покинувших

---

## 📝 ОТЧЁТ

Создай отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Миграция member_events

## Выполнено:
- [ ] alembic/versions/002_member_events.py создана
- [ ] Миграция применена
- [ ] Таблица существует
- [ ] Бот перезапущен

## Тесты:
- Таблица: ✅/❌
- Выход фиксируется: ✅/❌
- Отчёт верный: ✅/❌

## Версия протокола: 5.2.1
## Статус: [ГОТОВО / ПРОБЛЕМЫ]
```

---

**Жду выполнения!**
