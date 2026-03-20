"""
Обработчики админ-панели.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.utils.logger import logger


router = Router()


class AdminSendWelcomeStates(StatesGroup):
    """Состояния для отправки приветствия."""

    waiting_for_user = State()


def get_welcome_message_text() -> str:
    """Текст приветственного сообщения."""
    return (
        "👋 Приветствие от админа!\n\n"
        "Я бот ОТЧЕБОТ — помогаю пользователям IT-сферы.\n\n"
        "Если у вас есть проблема — пройдите исповедь.\n"
        "Нажмите /start чтобы начать."
    )


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-панель."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_back_to_menu")]
        ]
    )


@router.callback_query(F.data == "admin_send_welcome")
async def admin_send_welcome_start(callback: CallbackQuery, state: FSMContext):
    """Админ нажал 'Отправить приветствие'."""
    user_id = callback.from_user.id

    if user_id not in settings.admin_ids_list:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.answer(
        "📢 <b>Отправить приветствие</b>\n\n"
        "Перешлите сообщение пользователя или введите его Telegram ID:\n\n"
        "<i>Отмена: /cancel</i>",
        parse_mode="HTML",
        reply_markup=get_back_to_admin_keyboard(),
    )

    await state.set_state(AdminSendWelcomeStates.waiting_for_user)
    await callback.answer()


@router.message(AdminSendWelcomeStates.waiting_for_user)
async def process_welcome_target(message: Message, state: FSMContext):
    """Получатель для приветствия определён."""
    target_user_id = None
    input_text = message.text.strip() if message.text else ""

    if message.forward_from:
        target_user_id = message.forward_from.id
    elif message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif input_text.isdigit():
        target_user_id = int(input_text)
    else:
        await message.answer(
            "❌ Не удалось определить пользователя.\n"
            "Перешлите сообщение или введите числовой Telegram ID."
        )
        return

    try:
        welcome_text = get_welcome_message_text()
        await message.bot.send_message(
            chat_id=target_user_id,
            text=welcome_text,
        )
        await message.answer(
            f"✅ Приветствие отправлено пользователю {target_user_id}",
            reply_markup=get_back_to_admin_keyboard(),
        )
        logger.info(f"Админ отправил приветствие пользователю {target_user_id}")
    except Exception as e:
        await message.answer(
            f"❌ Ошибка отправки: {e}",
            reply_markup=get_back_to_admin_keyboard(),
        )
        logger.warning(f"Не удалось отправить приветствие {target_user_id}: {e}")

    await state.clear()


@router.message(Command("cancel"))
async def cancel_state(message: Message, state: FSMContext):
    """Отмена текущего состояния FSM."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("❌ Действие отменено.")
        logger.info(f"User {message.from_user.id} cancelled state: {current_state}")
