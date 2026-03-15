# Инструкция для Opencode Agent

**Версия протокола:** 1.2.0
**Приоритет:** КРИТИЧЕСКИЙ
**Дата:** 2026-03-15

---

## 📋 ЗАДАЧА: Пуш кода на GitHub

Репозиторий создан: https://github.com/adolfass/otchebot

---

## 🚀 ВЫПОЛНИ ПУШ КОДА

```bash
cd /project/otchebot

# Настроить git
git config user.email "romabo51@gmail.com"
git config user.name "adolfass"

# Проверить remote (должен быть origin)
git remote -v

# Если нет remote - добавить
git remote add origin git@github.com:adolfass/otchebot.git

# Переименовать ветку в main
git branch -M main

# Запушить код
git push -u origin main
```

---

## ✅ ПРОВЕРКА

```bash
# Проверить коммиты на GitHub
gh repo view adolfass/otchebot

# Или curl
curl -s https://api.github.com/repos/adolfass/otchebot/commits | head -20
```

---

## 📝 ОТЧЁТ

Создай отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Пуш кода на GitHub

## Выполнено:
- [ ] Код запушен на GitHub
- [ ] Репозиторий: https://github.com/adolfass/otchebot

## Коммиты:
- [список коммитов]

## Версия протокола: 1.2.1
## Статус: [ГОТОВО / ПРОБЛЕМЫ]
```

---

**Жду выполнения!**
