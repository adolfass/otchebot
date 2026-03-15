"""
Обработчики для группы комментариев канала.
"""

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import settings
from bot.database.crud import Database, MemberEventCRUD
from bot.database.models import MemberEventType
from bot.utils.logger import logger

router = Router()

GROUP_ID = None
db: Database = None


def init_group_handlers(database: Database):
    """Инициализация БД для группы."""
    global db
    db = database


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
    """Бот добавлен/удален из группы/канала."""
    global GROUP_ID
    
    # Импорт для избежания циклической зависимости
    from bot.handlers.common import set_channel_id
    
    if event.new_chat_member.status == "administrator":
        logger.info(f"Бот добавлен как админ в чат: {event.chat.title} (ID: {event.chat.id})")
        GROUP_ID = event.chat.id
        set_channel_id(event.chat.id)
    elif event.new_chat_member.status == "left" or event.new_chat_member.status == "kicked":
        logger.info(f"Бот удален из чата: {event.chat.title} (ID: {event.chat.id})")
        GROUP_ID = None


@router.chat_member()
async def handle_chat_member_update(event: types.ChatMemberUpdated):
    """Отслеживание изменений участников группы."""
    global db
    
    if db is None:
        return
    
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status
    
    user = event.new_chat_member.user
    
    async with db.async_session_factory() as session:
        crud = MemberEventCRUD(session)
        
        if str(old_status) in ["left", "kicked", "banned"] and str(new_status) == "member":
            await crud.create(
                user_id=user.id,
                event_type=MemberEventType.JOINED,
                chat_id=event.chat.id,
                username=user.username,
                first_name=user.first_name,
            )
            logger.info(f"Участник присоединился: {user.id} ({user.first_name})")
            
        elif str(new_status) in ["left", "kicked", "banned"]:
            await crud.create(
                user_id=user.id,
                event_type=MemberEventType.LEFT,
                chat_id=event.chat.id,
                username=user.username,
                first_name=user.first_name,
            )
            logger.info(f"Участник покинул: {user.id} ({user.first_name})")


@router.message(F.new_chat_members)
async def new_member_joined(message: types.Message):
    """Новый участник в группе."""
    global db
    
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        
        if db:
            async with db.async_session_factory() as session:
                crud = MemberEventCRUD(session)
                await crud.create(
                    user_id=member.id,
                    event_type=MemberEventType.JOINED,
                    chat_id=message.chat.id,
                    username=member.username,
                    first_name=member.first_name,
                )
        
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
    # Бот работает в группе, супергруппе и канале
    if message.chat.type not in ["group", "supergroup", "channel"]:
        return
    
    text = message.text or ""
    
    # Только явные триггеры: /help, #help, help или @mention бота
    has_trigger = False
    
    # Проверяем команду /help
    if text.startswith("/help"):
        has_trigger = True
    
    # Проверяем #help
    if "#help" in text.lower():
        has_trigger = True
    
    # Проверяем слово help (отдельно стоящее)
    import re
    if re.search(r'\bhelp\b', text.lower()):
        has_trigger = True
    
    # Проверяем упоминание @otchebot_bot
    bot_info = await message.bot.get_me()
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = text[entity.offset:entity.offset + entity.length]
                if mention_text == f"@{bot_info.username}":
                    has_trigger = True
                    break
    
    has_bot_username = "@otchebot_bot" in text or "@otche_bot" in text
    
    if has_trigger or has_bot_username:
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
