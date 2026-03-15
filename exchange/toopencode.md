# Инструкция для Opencode Agent

**Версия протокола:** 1.6.0
**Приоритет:** КРИТИЧЕСКИЙ
**Дата:** 2026-03-15

---

## 📋 ЗАДАЧА: Исправление Dockerfile.api и перезапуск

---

## 🐛 ПРОБЛЕМА

API не запускается: `ModuleNotFoundError: No module named 'bot'`

---

## ✅ ШАГ 1: ИСПРАВЬ Dockerfile.api

```bash
cd /project/otchebot

cat > Dockerfile.api << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

---

## 🚀 ШАГ 2: ПЕРЕЗАПУСК DOCKER COMPOSE

```bash
cd /project/otchebot

# Пересобрать API
docker-compose up -d --build api

# Проверить
docker-compose ps
docker-compose logs api
```

---

## 📝 ШАГ 3: ПРОВЕРКИ

```bash
# API Health check (из контейнера)
docker-compose exec api curl http://localhost:8000/health

# Или напрямую
curl http://89.125.53.65:8000/health

# Бот
docker-compose logs bot | tail -20
```

---

## 🔄 ШАГ 4: GIT PUSH

```bash
cd /project/otchebot

git config user.email "romabo51@gmail.com"
git config user.name "adolfass"

git add -A
git commit -m "fix: Dockerfile.api и PYTHONPATH"
git push origin main
```

---

## 📝 ОТЧЁТ

Создай отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Исправление Dockerfile.api

## Выполнено:
- [ ] Dockerfile.api исправлен
- [ ] API работает
- [ ] Изменения запушены

## Тесты:
- API Health: ✅/❌
- Бот работает: ✅/❌

## Версия протокола: 1.6.1
## Статус: [ГОТОВО / ПРОБЛЕМЫ]
```

---

**Жду выполнения!**
