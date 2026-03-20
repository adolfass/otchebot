"""
Обработчики админ-панели.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.utils.logger import logger
from bot.handlers.context import get_channel_id


router = Router()


def get_channel_greeting_text() -> str:
    """Текст приветственного сообщения для канала."""
    return """🎉 <b>Добрый день, подписчики!</b> 👋

━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>Рад приветствовать вас на канале IT ПРОПОВЕДНИК!</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━

📢 <b>Я — бот для приёма исповедей</b> от пользователей о наболевшем из мира IT.

━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 <b>Что я принимаю:</b>
• Жалобы и проблемы с техникой
• Вопросы про сайты, боты, программы
• Просьбы о помощи в IT-сфере

━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Примеры:</b>

▸ «У меня не работает принтер, айтишник говорит — нужно покупать новый! А я подозреваю, что меня пытаются обмануть!»

▸ «Мне нужен сайт! Сколько это будет стоить?»

▸ «Мне нужен бот для бизнеса!»

▸ «Нужен #help с сервером!»

━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 <b>Ваши заявки будут обработаны</b> — мы разберёмся, какие проблемы беспокоят предпринимателей и найдём решение вместе!

━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 <b>КАК ПОЛЬЗОВАТЬСЯ:</b>
1️⃣ Нажмите кнопку ниже
2️⃣ Перейдите к @otchebot_bot
3️⃣ Нажмите /start
4️⃣ Опишите вашу проблему
5️⃣ Подтвердите отправку

<b>Всё просто — справится даже ребёнок!</b> 👶

━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 <b>НАПИШИ /help или #help</b> — если нужна срочная помощь!"""


def get_channel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для сообщения в канале."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Начать исповедь", url="https://t.me/otchebot_bot")]
        ]
    )


@router.callback_query(F.data == "admin_send_welcome")
async def admin_send_welcome(callback: CallbackQuery):
    """Админ нажал 'Отправить приветствие в канал'."""
    user_id = callback.from_user.id

    if user_id not in settings.admin_ids_list:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    channel_id = get_channel_id()
    if channel_id is None:
        await callback.message.answer("❌ Канал не настроен. Добавьте бота в канал как админа или укажите CHANNEL_ID в .env.")
        await callback.answer()
        return

    try:
        greeting_text = get_channel_greeting_text()
        await callback.bot.send_message(
            chat_id=channel_id,
            text=greeting_text,
            reply_markup=get_channel_keyboard(),
            parse_mode="HTML"
        )
        await callback.message.answer("✅ Приветственное сообщение отправлено в канал!")
        logger.info(f"Приветствие отправлено в канал {channel_id}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Не удалось отправить приветствие: {e}")

    await callback.answer()
