"""
Обработчики команд и сообщений.
"""

from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from bot.config import settings
from bot.database.crud import Database, ComplaintCRUD
from bot.database.models import ComplaintStatus
from bot.services.form import ConfessionStates, FormService, AntiFloodService
from bot.services.user_data import UserDataCollector
from bot.utils.logger import logger
from bot.utils.validators import validate_confession_text, sanitize_text


# Создаём роутеры
router = Router()

# Глобальные сервисы (инициализируются в main.py)
db: Database = None
form_service: FormService = None
user_data_collector: UserDataCollector = None

# ID канала для приветствия
CHANNEL_ID = None


def set_channel_id(chat_id: int):
    """Установка ID канала."""
    global CHANNEL_ID
    CHANNEL_ID = chat_id


def init_handlers(
    database: Database,
    form_svc: FormService,
    collector: UserDataCollector,
):
    """Инициализация глобальных сервисов для хендлеров."""
    global db, form_service, user_data_collector
    db = database
    form_service = form_svc
    user_data_collector = collector


# ==================== КЛАВИАТУРЫ ====================


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для команды /start."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✨ Начать исповедь")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


def get_consent_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для запроса согласия."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Согласен", callback_data="consent_yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="consent_no"),
            ]
        ]
    )
    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Новые заявки", callback_data="admin_new")],
            [InlineKeyboardButton(text="📢 Отправить приветствие", callback_data="admin_send_welcome")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        ]
    )
    return keyboard


def get_complaint_keyboard(complaint_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для карточки заявки."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Отметить как обработанное",
                    callback_data=f"admin_process_{complaint_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад", callback_data="admin_new_back"
                )
            ],
        ]
    )
    return keyboard


# ==================== ОБРАБОТЧИКИ ====================


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    await state.clear()

    user_id = message.from_user.id

    # Если админ - показываем админ-панель
    if user_id in settings.admin_ids_list:
        welcome_text = (
            "👋 <b>Добро пожаловать, администратор!</b>\n\n"
            "Вы находитесь в панели управления ботом ОТЧЕБОТ."
        )
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_admin_keyboard(),
        )
        logger.info(f"Admin {user_id} started the bot")
        return

    # Для обычных пользователей - приветствие с исповедью
    welcome_text = (
        "✨ <b>Добро пожаловать в ОТЧЕБОТ!</b>\n\n"
        "Это бот для сбора исповедей — свободных описаний проблем в IT-сфере.\n\n"
        "Ваши ответы помогут получить помощь от специалистов и улучшить сообщество.\n\n"
        "<i>Все данные анонимны и используются только для обработки заявок.</i>"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_start_keyboard(),
    )

    logger.info(f"User {user_id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    user_id = message.from_user.id
    
    if user_id in settings.admin_ids_list:
        help_text = (
            "📖 <b>Команды администратора:</b>\n\n"
            "/start - Админ-панель\n"
            "/admin - Админ-панель\n"
            "/приветствие - Отправить приветствие в канал\n"
            "/test_report - Тестовый отчёт\n"
            "/help - Эта справка"
        )
    else:
        help_text = (
            "📖 <b>Команды бота:</b>\n\n"
            "/start - Начать новую исповедь\n"
            "/delete_my_data - Удалить все мои заявки\n"
            "/help - Эта справка"
        )

    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("delete_my_data"))
async def cmd_delete_my_data(message: Message):
    """Обработчик команды /delete_my_data (право на забвение)."""
    user_id = message.from_user.id

    async with db.async_session_factory() as session:
        crud = ComplaintCRUD(session)
        deleted_count = await crud.delete_by_user_id(user_id)

    if deleted_count > 0:
        await message.answer(
            f"✅ Удалено заявок: {deleted_count}\n\n"
            "Все ваши данные были удалены из базы."
        )
        logger.info(f"User {user_id} deleted {deleted_count} complaints")
    else:
        await message.answer("У вас нет заявок в базе.")

    logger.info(f"User {user_id} requested data deletion")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Обработчик команды /admin (админ-панель)."""
    user_id = message.from_user.id

    # Проверка прав администратора
    if user_id not in settings.admin_ids_list:
        await message.answer("❌ Доступ запрещён.")
        logger.warning(f"Unauthorized admin access attempt from user {user_id}")
        return

    await message.answer(
        "🔧 **Админ-панель**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(),
    )

    logger.info(f"Admin {user_id} opened admin panel")


@router.message(Command("приветствие"))
async def cmd_greeting(message: Message):
    """Отправка приветственного сообщения в канал."""
    global CHANNEL_ID
    
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ Доступ запрещён.")
        return
    
    if CHANNEL_ID is None:
        await message.answer("❌ Канал не настроен. Добавьте бота в канал как админа.")
        return
    
    greeting_text = """🎉 <b>Добрый день, подписчики!</b> 👋

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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Начать исповедь", url="https://t.me/otchebot_bot")]
        ]
    )
    
    try:
        await message.bot.send_message(chat_id=CHANNEL_ID, text=greeting_text, reply_markup=keyboard, parse_mode="HTML")
        await message.answer("✅ Приветственное сообщение отправлено в канал!")
        logger.info(f"Приветствие отправлено в канал {CHANNEL_ID}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Не удалось отправить приветствие: {e}")


@router.message(F.text == "✨ Начать исповедь")
async def start_confession(message: Message, state: FSMContext):
    """Начало процесса сбора исповеди."""
    user_id = message.from_user.id

    # Проверка антифлуда
    can_proceed, error_msg = await form_service.start_confession(user_id, state)
    if not can_proceed:
        await message.answer(f"⏳ {error_msg}")
        return

    await state.set_state(ConfessionStates.waiting_text)

    await message.answer(
        "📝 **Введите вашу проблему**\n\n"
        "Опишите ситуацию подробно, но без персональных данных.\n"
        f"_Максимальная длина: {FormService.MAX_TEXT_LENGTH} символов._\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="Markdown",
    )

    logger.info(f"User {user_id} started confession process")


@router.message(ConfessionStates.waiting_text, F.text)
async def process_confession_text(message: Message, state: FSMContext):
    """Обработка текста исповеди."""
    user_id = message.from_user.id
    text = sanitize_text(message.text)

    # Валидация
    is_valid, error_msg = validate_confession_text(text, FormService.MAX_TEXT_LENGTH)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\n\nПопробуйте ещё раз.")
        return

    # Сохраняем текст во временное хранилище
    await state.update_data(confession_text=text)
    await state.set_state(ConfessionStates.waiting_consent)

    # Запрос согласия
    await message.answer(
        "🔒 **Согласие на обработку данных**\n\n"
        "Для обработки заявки мы можем сохранить:\n"
        "• Ваш Telegram ID\n"
        "• Username (если есть)\n"
        "• Имя и фамилию\n"
        "• Фото профиля (если есть)\n\n"
        "_Эти данные помогут идентифицировать вас при обратной связи._",
        parse_mode="Markdown",
        reply_markup=get_consent_keyboard(),
    )

    logger.info(f"User {user_id} submitted confession text")


@router.callback_query(F.data == "consent_yes")
async def process_consent_yes(callback: CallbackQuery, state: FSMContext):
    """Обработка согласия на сбор данных."""
    user_id = callback.from_user.id

    # Получаем данные из состояния
    data = await state.get_data()
    text = data.get("confession_text")

    if not text:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        await state.clear()
        return

    # Собираем данные профиля
    username, first_name, last_name, photo_file_id = await user_data_collector.get_user_data(
        user_id
    )

    # Сохраняем в БД
    async with db.async_session_factory() as session:
        crud = ComplaintCRUD(session)
        complaint = await crud.create(
            user_id=user_id,
            text=text,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_file_id=photo_file_id,
        )

    await state.clear()

    # Ответ пользователю
    await callback.message.answer(
        "✅ **Ваша заявка принята!**\n\n"
        "Она будет обработана в ближайшее время.\n\n"
        "_Сейчас бот в тестовом режиме, время обработки до 2 суток._\n"
        "Спасибо за понимание! 🙏",
        parse_mode="Markdown",
    )

    logger.info(f"Complaint saved: id={complaint.id}, user_id={user_id}")
    await callback.answer()


@router.callback_query(F.data == "consent_no")
async def process_consent_no(callback: CallbackQuery, state: FSMContext):
    """Обработка отказа от сбора данных."""
    await state.clear()

    await callback.message.answer(
        "❌ Заявка не была создана.\n\n"
        "Вы можете начать заново командой /start"
    )

    logger.info(f"User {callback.from_user.id} declined consent")
    await callback.answer()


@router.callback_query(F.data == "admin_new")
async def admin_show_new(callback: CallbackQuery):
    """Показ новых заявок (админка)."""
    user_id = callback.from_user.id

    if user_id not in settings.admin_ids_list:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async with db.async_session_factory() as session:
        crud = ComplaintCRUD(session)
        complaints, total = await crud.get_new(limit=1, offset=0)

    if not complaints:
        await callback.message.answer("📭 Нет новых заявок.")
        await callback.answer()
        return

    complaint = complaints[0]
    await show_complaint_card(callback.message, complaint)
    await callback.answer()


async def show_complaint_card(message: Message, complaint):
    """Показ карточки заявки."""
    photo_caption = (
        f"📋 **Заявка #{complaint.id}**\n\n"
        f"👤 **Пользователь:**\n"
        f"• ID: `{complaint.user_id}`\n"
        f"• Username: @{complaint.username or 'нет'}\n"
        f"• Имя: {complaint.first_name or 'нет'} {complaint.last_name or ''}\n\n"
        f"📝 **Текст:**\n{complaint.text}\n\n"
        f"🕒 **Дата:** {complaint.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if complaint.photo_file_id:
        await message.answer_photo(
            photo=complaint.photo_file_id,
            caption=photo_caption,
            parse_mode="Markdown",
            reply_markup=get_complaint_keyboard(complaint.id),
        )
    else:
        await message.answer(
            photo_caption,
            parse_mode="Markdown",
            reply_markup=get_complaint_keyboard(complaint.id),
        )


@router.callback_query(F.data.startswith("admin_process_"))
async def admin_process_complaint(callback: CallbackQuery):
    """Обработка заявки администратором."""
    user_id = callback.from_user.id

    if user_id not in settings.admin_ids_list:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    complaint_id = int(callback.data.split("_")[-1])

    async with db.async_session_factory() as session:
        crud = ComplaintCRUD(session)
        complaint = await crud.mark_as_processed(complaint_id)

    if complaint:
        await callback.message.edit_caption(
            caption=f"✅ **Заявка #{complaint.id} обработана**\n\n"
            f"Статус: PROCESSED",
            parse_mode="Markdown",
        )
        logger.info(f"Admin {user_id} processed complaint {complaint_id}")
    else:
        await callback.answer("❌ Заявка не найдена", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_show_stats(callback: CallbackQuery):
    """Показ статистики (админка)."""
    user_id = callback.from_user.id

    if user_id not in settings.admin_ids_list:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async with db.async_session_factory() as session:
        crud = ComplaintCRUD(session)
        stats = await crud.get_statistics(days=7)

    stats_text = (
        "📊 **Статистика за 7 дней**\n\n"
        f"📭 Новые: {stats.get('new', 0)}\n"
        f"📤 Отправленные: {stats.get('sent', 0)}\n"
        f"✅ Обработанные: {stats.get('processed', 0)}\n"
        f"📈 **Всего:** {stats.get('total', 0)}"
    )

    await callback.message.answer(stats_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "admin_new_back")
async def admin_back_to_menu(callback: CallbackQuery):
    """Возврат в меню админки."""
    await callback.message.answer(
        "🔧 **Админ-панель**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего состояния."""
    await state.clear()
    await message.answer(
        "❌ Отменено.\n\nДля начала новой исповеди нажмите /start",
        reply_markup=get_start_keyboard(),
    )
    logger.info(f"User {message.from_user.id} cancelled confession")
