"""Customer command handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import config
from database import users
from keyboards.customer import get_main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with optional referral code."""
    db = message.bot['db']
    
    # Extract referral code from deep link
    referral_code = None
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
    
    # Check if user exists
    user = await users.get_user_by_telegram_id(db, message.from_user.id)
    
    if not user:
        # Create new user
        await users.create_user(
            db,
            message.from_user.id,
            message.from_user.username,
            referral_code
        )
    
    # Send welcome message
    await message.answer(
        config.WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """🔥 Arriva Shop KZ v4.0 — Помощь

📱 Команды:
/start — Главное меню
/referral — Реферальная программа
/help — Эта справка

💨 Как заказать:
1. Выбери товар из каталога
2. Выбери вкус и количество
3. Оформи заказ
4. Выбери способ оплаты

💎 Способы оплаты:
• Kaspi — переводом на карту
• Встреча — наличными при встрече

🚚 Доставка:
• Алматы, Астана — от 2 часов
• Шымкент, Караганда — на следующий день

💰 Реферальная программа:
Приведи друга — получи 500₸ на Kaspi!

Братан, если вопросы — пиши админам! 🔥"""
    
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Show main menu."""
    await callback.message.edit_text(
        config.WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Show help via callback."""
    help_text = """🔥 Arriva Shop KZ v4.0 — Помощь

📱 Команды:
/start — Главное меню
/referral — Реферальная программа
/help — Эта справка

💨 Как заказать:
1. Выбери товар из каталога
2. Выбери вкус и количество
3. Оформи заказ
4. Выбери способ оплаты

💎 Способы оплаты:
• Kaspi — переводом на карту
• Встреча — наличными при встрече

🚚 Доставка:
• Алматы, Астана — от 2 часов
• Шымкент, Караганда — на следующий день

💰 Реферальная программа:
Приведи друга — получи 500₸ на Kaspi!

Братан, если вопросы — пиши админам! 🔥"""
    
    await callback.message.edit_text(help_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()
