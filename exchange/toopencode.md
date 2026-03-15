# Инструкция для Opencode Agent

**Версия протокола:** 1.0.0
**Приоритет:** ВЫСОКИЙ
**Дата:** 2026-03-15

---

## 📋 ЗАДАЧА: Этап 1 - Настройка окружения и структуры проекта

Qwen Code завершил создание базовой структуры проекта ОТЧЕБОТ.

---

## 📂 ЧТО БЫЛО СОЗДАНО

### Файлы конфигурации:
- `.env.example` — пример переменных окружения
- `.gitignore` — игнорируемые файлы
- `requirements.txt` — Python зависимости

### Docker:
- `Dockerfile.bot` — образ для Telegram бота
- `Dockerfile.api` — образ для API сервера
- `docker-compose.yml` — оркестрация сервисов

### Код бота (bot/):
- `bot/main.py` — точка входа
- `bot/config.py` — настройки
- `bot/database/models.py` — SQLAlchemy модели
- `bot/database/crud.py` — CRUD операции
- `bot/services/form.py` — FSM и антифлуд
- `bot/services/user_data.py` — сбор данных профиля
- `bot/handlers/common.py` — обработчики команд
- `bot/utils/logger.py` — логирование
- `bot/utils/validators.py` — валидаторы

### Код API (api/):
- `api/server.py` — FastAPI приложение
- `api/routes.py` — эндпоинты
- `api/dependencies.py` — зависимости (авторизация)

### Скрипты (scripts/):
- `scripts/setup_replication.sh` — настройка репликации PostgreSQL
- `scripts/backup.sh` — ежедневные бэкапы

### Миграции БД (alembic/):
- `alembic.ini` — конфигурация Alembic
- `alembic/env.py` — окружение миграций
- `alembic/versions/001_initial.py` — начальная миграция

---

## 🚀 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА СЕРВЕРЕ

### 1. Подготовка окружения

```bash
# Перейти в директорию проекта
cd /project/otchebot

# Инициализировать git репозиторий (если ещё не создан)
git init
git remote add origin git@github.com:your-repo/otchebot.git

# Добавить все файлы
git add -A

# Сделать первый коммит
git commit -m "feat: initial project structure

- Bot (aiogram 3.x) с FSM и антифлудом
- API (FastAPI) с pull-механизмом
- PostgreSQL + Alembic миграции
- Docker контейнеризация
- Скрипты репликации и бэкапов

Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>"

# Отправить на GitHub
git push -u origin main
```

### 2. Настройка переменных окружения

```bash
# Создать .env файл на основе .env.example
cp .env.example .env

# Отредактировать .env (заполнить реальными значениями)
nano .env
```

**Обязательные переменные:**
```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=postgresql+asyncpg://otchebot_user:secure_password@postgres:5432/otchebot
EXTERNAL_API_KEY=your_secret_api_key_here
POSTGRES_PASSWORD=secure_password_here
```

### 3. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f bot
docker-compose logs -f api
docker-compose logs -f postgres
```

### 4. Применение миграций БД

```bash
# Миграции применяются автоматически при старте контейнеров
# Но можно применить вручную:

# Внутри контейнера бота
docker-compose exec bot python -c "from bot.database.crud import Database; import asyncio; asyncio.run(Database('postgresql+asyncpg://otchebot_user:secure_password@postgres:5432/otchebot').create_tables())"

# Или через Alembic
docker-compose exec bot alembic upgrade head
```

---

## ✅ ПРОВЕРКИ ПОСЛЕ ДЕПЛОЯ

### 1. Проверка бота

```bash
# Лог бота
docker-compose logs bot | tail -50

# Ожидается:
# - "Бот запущен: @your_bot_username"
# - "Таблицы БД созданы/проверены"
```

### 2. Проверка API

```bash
# Health check
curl http://localhost:8000/health

# Ожидается: {"status":"ok","version":"1.0.0"}

# Корневой эндпоинт
curl http://localhost:8000/

# Ожидается: {"message":"OTCHÉBOT API","docs":"/docs","health":"/health"}

# Swagger документация
# Открыть в браузере: http://your-server-ip:8000/docs
```

### 3. Проверка базы данных

```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U otchebot_user -d otchebot -c "\dt"

# Ожидается таблица: complaints

# Проверка структуры
docker-compose exec postgres psql -U otchebot_user -d otchebot -c "\d complaints"
```

### 4. Проверка API с авторизацией

```bash
# Получить API ключ из .env
API_KEY=$(grep EXTERNAL_API_KEY .env | cut -d'=' -f2)

# Тестовый запрос к API
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/problems

# Ожидается: {"items":[],"total":0,"limit":100,"offset":0}
```

---

## 🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА

### Тест 1: Команда /start

1. Открыть Telegram
2. Найти бота по токену
3. Отправить `/start`
4. **Ожидается:** Приветственное сообщение + кнопка "✨ Начать исповедь"

### Тест 2: Начало исповеди

1. Нажать кнопку "✨ Начать исповедь"
2. **Ожидается:** Сообщение с просьбой ввести текст проблемы

### Тест 3: Отправка текста

1. Ввести текст проблемы (до 500 символов)
2. **Ожидается:** Запрос согласия на сбор данных (кнопки ✅/❌)

### Тест 4: Согласие на данные

1. Нажать "✅ Согласен"
2. **Ожидается:** Сообщение "Ваша заявка принята!..."

### Тест 5: Админ-панель

1. Отправить `/admin` (с аккаунта из ADMIN_IDS)
2. **Ожидается:** Меню админки с кнопками "📨 Новые заявки" и "📊 Статистика"

### Тест 6: API запрос

```bash
# Получить новые заявки
curl -H "X-API-Key: YOUR_KEY" "http://localhost:8000/api/v1/problems?status=new"

# Ожидается: JSON с заявками
```

---

## 📝 ОТЧЁТ

После выполнения напиши отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Этап 1 - Настройка структуры проекта

## Выполнено:
- [ ] Git репозиторий инициализирован
- [ ] Код запушен на GitHub
- [ ] .env настроен
- [ ] Docker-compose запущен
- [ ] Миграции применены

## Тесты:
- Health check API: ✅/❌
- Бот отвечает на /start: ✅/❌
- База данных создана: ✅/❌

## Проблемы:
1. [описание если есть]

## Логи:
[ключевые сообщения об ошибках если есть]

## Версия протокола: 1.0.1
## Статус: [ГОТОВО / ТРЕБУЕТ ИСПРАВЛЕНИЯ]
```

---

## 🔧 ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### Проблема: Docker не запускается
```bash
# Проверить Docker
docker --version
docker-compose --version

# Перезапустить Docker
sudo systemctl restart docker
```

### Проблема: Ошибка подключения к БД
```bash
# Проверить .env
cat .env | grep DATABASE_URL

# Проверить контейнер PostgreSQL
docker-compose exec postgres psql -U otchebot_user -d otchebot -c "SELECT 1"
```

### Проблема: Бот не отвечает
```bash
# Проверить токен бота
cat .env | grep BOT_TOKEN

# Посмотреть логи
docker-compose logs bot | tail -100
```

### Проблема: Миграции не применяются
```bash
# Применить вручную
docker-compose exec bot alembic upgrade head

# Проверить статус миграций
docker-compose exec bot alembic current
```

---

## 📞 СВЯЗЬ

При возникновении проблем:
1. Запиши ошибку в отчёт
2. Qwen Code проанализирует и даст инструкцию по исправлению

---

**Инструкция создана:** Qwen Code
**Для:** Opencode Agent
**Проект:** ОТЧЕБОТ (@otche_bot)
