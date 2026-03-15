"""
Обработчики для группы комментариев канала.
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import settings
from bot.utils.logger import logger

router = Router()

GROUP_ID = None


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✨ Пройти исповедь",
            url="https://t.me/otchebot_bot"
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


@router.my_chat_member()
async def bot_added_to_group(event: types.ChatMemberUpdated):
    """Бот добавлен в группу/канал."""
    if event.new_chat_member.status == "administrator":
        logger.info(f"Бот добавлен как админ в чат: {event.chat.title} (ID: {event.chat.id})")
        global GROUP_ID
        GROUP_ID = event.chat.id


@router.message(F.new_chat_members)
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
        
        await message.answer(
            welcome_text,
            reply_markup=get_welcome_keyboard()
        )
        logger.info(f"Приветствие нового участника: {member.id}")


@router.callback_query(F.data == "welcome_later")
async def welcome_later_callback(callback: types.CallbackQuery):
    """Пользователь нажал 'Позже'."""
    await callback.message.delete()
    await callback.answer("Хорошо, обращайтесь в любое время!")


@router.message()
async def handle_help_keywords(message: types.Message):
    """Реакция на ключевые слова и упоминания в группе."""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    text = message.text or ""
    keywords = ["помогите", "исповедь", "помощь", "help", "помощ"]
    
    bot_info = await message.bot.get_me()
    has_mention = False
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = text[entity.offset:entity.offset + entity.length]
                if mention_text == f"@{bot_info.username}":
                    has_mention = True
                    break
    
    has_keyword = any(kw in text.lower() for kw in keywords)
    has_bot_username = "@otchebot_bot" in text or "@otche_bot" in text
    
    if has_mention or has_keyword or has_bot_username:
        try:
            await message.delete()
            logger.info(f"Удалено сообщение от {message.from_user.id}")
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
        
        help_text = (
            "👋 Я увидел ваш призыв о помощи!\n\n"
            "Давайте заполним форму исповеди — это поможет специалистам "
            "лучше понять вашу проблему.\n\n"
            "Нажмите /start или перейдите в бота: @otchebot_bot"
        )
        
        try:
            await message.bot.send_message(chat_id=message.from_user.id, text=help_text)
            logger.info(f"Отправлена помощь пользователю {message.from_user.id}")
        except Exception as e:
            logger.warning(f"Не удалось отправить ЛС: {e}")
