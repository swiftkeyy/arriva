"""Customer command handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import config
from database import users, orders
from keyboards.customer import get_main_menu_keyboard
from database.db_instance import get_db

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with optional referral code."""
    db = get_db()
    
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


@router.message(Command("myorders"))
async def cmd_my_orders(message: Message):
    """Show user's active orders with cancel option."""
    db = get_db()
    user = await users.get_user_by_telegram_id(db, message.from_user.id)
    if not user:
        await message.answer("Сначала запусти /start")
        return

    cursor = await db.execute(
        """SELECT order_number, status, total_amount, created_at
           FROM orders WHERE user_id = ? AND status NOT IN ('completed', 'cancelled')
           ORDER BY created_at DESC LIMIT 5""",
        (user['id'],)
    )
    rows = await cursor.fetchall()
    await cursor.close()

    if not rows:
        await message.answer("У тебя нет активных заказов.", reply_markup=get_main_menu_keyboard())
        return

    for row in rows:
        order = dict(row)
        status_map = {'pending': '🆕 Новый', 'confirmed': '✅ Подтверждён'}
        status_text = status_map.get(order['status'], order['status'])
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data=f"user_cancel_order_{order['order_number']}"
            )
        ]])
        await message.answer(
            f"📦 #{order['order_number']}\n"
            f"Статус: {status_text}\n"
            f"Сумма: {order['total_amount']}₸",
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("user_cancel_order_"))
async def user_cancel_order(callback: CallbackQuery):
    """User cancels their own order."""
    order_number = callback.data.replace("user_cancel_order_", "")
    db = get_db()

    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return

    # Проверяем что заказ принадлежит этому пользователю и ещё можно отменить
    cursor = await db.execute(
        "SELECT status, user_id FROM orders WHERE order_number = ?",
        (order_number,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if not row:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    if dict(row)['user_id'] != user['id']:
        await callback.answer("Это не твой заказ", show_alert=True)
        return
    if dict(row)['status'] not in ('pending', 'confirmed'):
        await callback.answer("Этот заказ уже нельзя отменить", show_alert=True)
        return

    from database.orders import cancel_order
    await cancel_order(db, order_number)

    # Уведомляем админов
    for admin_id in config.ADMIN_IDS:
        try:
            await callback.bot.send_message(
                admin_id,
                f"❌ Пользователь отменил заказ!\n\n"
                f"📦 #{order_number}\n"
                f"👤 @{callback.from_user.username or callback.from_user.id}"
            )
        except Exception:
            pass

    await callback.message.edit_text(f"✅ Заказ #{order_number} отменён.")
    await callback.answer("Заказ отменён")
