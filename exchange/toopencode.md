# Инструкция для Opencode Agent

**Версия протокола:** 4.0.0
**Приоритет:** ВЫСОКИЙ
**Дата:** 2026-03-15

---

## 📋 ЭТАП 4: Тестирование API для внешнего агента

API уже реализован. Нужно протестировать все эндпоинты.

---

## 🧪 ТЕСТЫ

### Подготовка

```bash
# Получить API ключ
API_KEY=$(grep EXTERNAL_API_KEY /project/otchebot/.env | cut -d'=' -f2)
echo "API Key: $API_KEY"

# Базовый URL
API_URL="http://localhost:8000/api/v1"
```

### Тест 1: Health Check

```bash
curl http://localhost:8000/health
```
**Ожидается:** `{"status":"ok","version":"1.0.0"}`

### Тест 2: Получить новые заявки

```bash
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?status=new&limit=10&offset=0"
```
**Ожидается:** JSON с заявками (может быть пустой массив)

### Тест 3: Получить заявку по ID

```bash
curl -H "X-API-Key: $API_KEY" "$API_URL/problems/1"
```
**Ожидается:** Объект заявки или 404

### Тест 4: Пометить заявку как sent

```bash
curl -X POST -H "X-API-Key: $API_KEY" "$API_URL/problems/1/mark_sent"
```
**Ожидается:** `{"id":1,"status":"sent"}`

### Тест 5: Неверный API ключ

```bash
curl -H "X-API-Key: wrong_key" "$API_URL/problems"
```
**Ожидается:** 401 Unauthorized

### Тест 6: Без API ключа

```bash
curl "$API_URL/problems"
```
**Ожидается:** 401 Unauthorized

### Тест 7: Пагинация

```bash
# Страница 1
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?limit=5&offset=0"

# Страница 2
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?limit=5&offset=5"
```

### Тест 8: Фильтр по статусу

```bash
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?status=processed"
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?status=sent"
```

### Тест 9: mark_as_sent=true в GET запросе

```bash
curl -H "X-API-Key: $API_KEY" "$API_URL/problems?mark_as_sent=true&limit=1"
```
**Ожидается:** Заявки автоматически помечаются как sent

---

## 📝 ОТЧЁТ

Создай отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Этап 4 - Тестирование API

## Тесты:
- Health Check: ✅/❌
- GET /problems: ✅/❌
- GET /problems/{id}: ✅/❌
- POST /problems/{id}/mark_sent: ✅/❌
- Неверный ключ (401): ✅/❌
- Без ключа (401): ✅/❌
- Пагинация: ✅/❌
- Фильтр по статусу: ✅/❌
- mark_as_sent: ✅/❌

## Пример ответа API:
```json
{...}
```

## Версия протокола: 4.0.1
## Статус: [ГОТОВО / ПРОБЛЕМЫ]
```

---

**Жду выполнения!**
