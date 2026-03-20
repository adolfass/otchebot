# Инструкция для Opencode Agent

**Версия протокола:** 5.0.0
**Приоритет:** ВЫСОКИЙ
**Дата:** 2026-03-20

---

## 📋 ЗАДАЧА: Улучшение функционала приветствий

---

## 🎯 ТРЕБОВАНИЯ

### 1. Кнопка "Приветствие" в админ-панели

**Где:** /admin меню

**Функция:**
- Кнопка "📢 Отправить приветствие"
- После нажатия — поле для ввода ID пользователя или пересылки сообщения
- Бот отправляет приветствие выбранному пользователю в ЛС

### 2. Автоскрытие приветствия через 60 секунд

**Логика:**
- Бот отправляет приветствие новому участнику
- Запускается таймер на 60 секунд
- Если пользователь **НЕ нажал** кнопку → сообщение удаляется автоматически
- Если пользователь **НАЖАЛ** кнопку → сообщение удаляется сразу

---

## 🔧 РЕАЛИЗАЦИЯ

### 1. Изменить `bot/handlers/group.py`

**Добавить таймер на удаление:**

```python
import asyncio

@router.new_chat_members()
async def new_member_joined(message: types.Message):
    """Новый участник в группе."""
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        
        welcome_text = (
            f"👋 Привет, {member.mention_html()}!\n\n"
            "Я бот ОТЧЕБОТ — помогаю пользователям IT-сферы.\n\n"
            "Если у вас есть проблема — пройдите исповедь."
        )
        
        sent_message = await message.answer(
            welcome_text,
            reply_markup=get_welcome_keyboard()
        )
        
        # Запланировать удаление через 60 секунд
        asyncio.create_task(delete_after_delay(sent_message, 60))
        
        logger.info(f"Приветствие нового участника: {member.id}")


async def delete_after_delay(message: types.Message, delay: int):
    """Удалить сообщение через задержку."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
        logger.info(f"Автоскрытие приветствия: {message.message_id}")
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")


@router.callback_query(F.data == "welcome_later")
async def welcome_later_callback(callback: types.CallbackQuery):
    """Пользователь нажал 'Позже'."""
    await callback.message.delete()
    await callback.answer("Хорошо, обращайтесь в любое время!")


@router.callback_query(F.data == "welcome_confession")
async def welcome_confession_callback(callback: types.CallbackQuery):
    """Пользователь нажал 'Пройти исповедь'."""
    await callback.message.delete()
    
    # Отправить инструкцию в ЛС
    await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text="✨ Добро пожаловать в ОТЧЕБОТ!\n\n"
             "Нажмите /start чтобы начать исповедь."
    )
    await callback.answer()
```

**Обновить клавиатуру:**

```python
def get_welcome_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✨ Пройти исповедь",
            callback_data="welcome_confession"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="⏳ Позже",
            callback_data="welcome_later"
        )
    )
    builder.adjust(2)
    return builder.as_markup()
```

### 2. Добавить в `bot/handlers/admin.py`

```python
@router.callback_query(F.data == "admin_send_welcome")
async def admin_send_welcome(callback: CallbackQuery):
    """Админ хочет отправить приветствие пользователю."""
    await callback.message.answer(
        "📢 Отправить приветствие\n\n"
        "Перешлите сообщение пользователя или введите его Telegram ID:"
    )
    await callback.answer()


@router.message(F.forward_from | F.reply_to_message)
async def process_welcome_target(message: Message, state: FSMContext):
    """Получатель для приветствия определён."""
    target_user = None
    
    if message.forward_from:
        target_user = message.forward_from.id
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user.id
    
    if target_user:
        try:
            await message.bot.send_message(
                chat_id=target_user,
                text="👋 Приветствие от админа!\n\n"
                     "Я бот ОТЧЕБОТ — помогаю пользователям IT-сферы.\n\n"
                     "Если у вас есть проблема — пройдите исповедь.\n"
                     "Нажмите /start чтобы начать.",
                reply_markup=get_welcome_keyboard()
            )
            await message.answer(f"✅ Приветствие отправлено пользователю {target_user}")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
```

### 3. Обновить меню админки

Добавить кнопку в `get_admin_keyboard()`:

```python
InlineKeyboardButton(text="📢 Отправить приветствие", callback_data="admin_send_welcome")
```

---

## 🧪 ТЕСТЫ

### Тест 1: Автоскрытие через 60 сек

1. Добавить нового бота в группу (для теста)
2. **Ожидается:** Через 60 сек приветствие удалится

### Тест 2: Кнопка "Позже"

1. Нажать "⏳ Позже"
2. **Ожидается:** Сообщение удаляется сразу

### Тест 3: Кнопка "Пройти исповедь"

1. Нажать "✨ Пройти исповедь"
2. **Ожидается:** 
   - Сообщение удаляется
   - В ЛС приходит инструкция

### Тест 4: Админ отправляет приветствие

1. /admin → "📢 Отправить приветствие"
2. Переслать сообщение пользователя
3. **Ожидается:** Пользователь получил приветствие в ЛС

---

## 📝 ОТЧЁТ

Создай отчёт в `exchange/toQwen.md`:

```markdown
# Отчёт Opencode Agent

## Задача: Улучшение приветствий

## Выполнено:
- [ ] Таймер на 60 секунд
- [ ] Кнопка "Пройти исповедь" (callback)
- [ ] Кнопка "Позже" (удаление)
- [ ] Админ-кнопка "Отправить приветствие"

## Тесты:
- Автоскрытие: ✅/❌
- Кнопки работают: ✅/❌
- Админ отправка: ✅/❌

## Версия протокола: 5.0.1
## Статус: [ГОТОВО / ПРОБЛЕМЫ]
```

---

**Жду выполнения!**
