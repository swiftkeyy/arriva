"""Checkout handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import cart, orders, users
from database.meetings import create_meeting, cancel_meeting_by_order
from database.cities import get_all_cities
from keyboards.customer import get_city_keyboard, get_payment_method_keyboard, get_main_menu_keyboard
from database.db_instance import get_db
import config

router = Router()


class CheckoutStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_payment_method = State()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Start checkout process."""
    db = get_db()
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    cart_items = await cart.get_user_cart(db, user['id'])
    
    if not cart_items:
        await callback.answer(config.ERROR_MESSAGES["empty_cart"], show_alert=True)
        return
    
    # Load cities from database
    cities = await get_all_cities(db)
    
    # Check for upsell opportunity
    total = sum(item['subtotal'] for item in cart_items)
    
    if total < 3000 and len(cart_items) == 1:
        upsell_text = f"""🛒 Твоя корзина: {total}₸

Братан, добавь ещё один товар и получи скидку 10%! 🔥

Или продолжай оформление 👇"""
        
        await callback.message.edit_text(upsell_text, reply_markup=get_city_keyboard(cities))
    
    await state.set_state(CheckoutStates.waiting_for_city)
    await callback.message.edit_text(
        "🏙 Выбери город доставки, братан! 🇰🇿",
        reply_markup=get_city_keyboard(cities)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("city_"))
async def select_city(callback: CallbackQuery, state: FSMContext):
    """Handle city selection."""
    city = callback.data.split("_")[1]
    await state.update_data(city=city)
    await state.set_state(CheckoutStates.waiting_for_address)
    
    await callback.message.edit_text(
        f"📍 Город: {city}\n\nТеперь напиши адрес доставки, братан!\n\nПример: ул. Абая 150, кв. 25"
    )
    await callback.answer()


@router.message(CheckoutStates.waiting_for_address)
async def receive_address(message: Message, state: FSMContext):
    """Handle address input."""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer(config.ERROR_MESSAGES["invalid_address"])
        return
    
    await state.update_data(address=address)
    await state.set_state(CheckoutStates.waiting_for_payment_method)
    
    await message.answer(
        "💳 Выбери способ оплаты, братан! 🔥",
        reply_markup=get_payment_method_keyboard()
    )


@router.callback_query(F.data == "payment_kaspi")
async def select_kaspi_payment(callback: CallbackQuery, state: FSMContext):
    """Handle Kaspi payment selection."""
    db = get_db()
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    data = await state.get_data()
    city = data['city']
    address = data['address']
    
    cart_items = await cart.get_user_cart(db, user['id'])
    
    try:
        order_number = await orders.create_order(
            db, user['id'], cart_items, city, address, 'kaspi'
        )
        
        total = sum(item['subtotal'] for item in cart_items)
        
        kaspi_text = f"""✅ Заказ #{order_number} создан!

💰 Сумма: {total}₸

💳 РЕКВИЗИТЫ KASPI:
📱 Номер: +7 777 030 07 83 
👤 Получатель: Бексултан А.

📝 В комментарии укажи: {order_number}

После оплаты отправь скриншот сюда! 📸

⏱ Подтверждение: 5-15 минут
🚚 Доставка: 2 часа (Алматы/Астана)

Погнали, братан! 🔥"""
        
        await callback.message.edit_text(kaspi_text)
        await state.clear()
        await callback.answer()

        # Уведомление всем админам
        username = callback.from_user.username or callback.from_user.first_name
        for admin_id in config.ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🛒 <b>Новый заказ!</b>\n\n"
                    f"📦 #{order_number}\n"
                    f"👤 @{username} (ID: {callback.from_user.id})\n"
                    f"💳 Оплата: Kaspi\n"
                    f"📍 Город: {city}\n"
                    f"💰 Сумма: {total}₸\n\n"
                    f"Подтверди оплату: /kaspi_paid {order_number}",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        
    except ValueError as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
        await state.clear()


@router.callback_query(F.data == "payment_meeting")
async def select_meeting_payment(callback: CallbackQuery, state: FSMContext):
    """Handle cash meeting payment selection."""
    db = get_db()
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    
    data = await state.get_data()
    city = data['city']
    address = data['address']
    
    cart_items = await cart.get_user_cart(db, user['id'])
    
    try:
        order_number = await orders.create_order(
            db, user['id'], cart_items, city, address, 'cash_meeting'
        )
        
        # Create meeting
        order = await orders.get_order_by_number(db, order_number)
        await create_meeting(db, order['id'], user['id'])
        
        total = sum(item['subtotal'] for item in cart_items)
        
        meeting_text = f"""✅ Заказ #{order_number} создан!

💰 Сумма: {total}₸
💵 Оплата: Наличными при встрече

📍 Город: {city}

Братан, сейчас админ свяжется с тобой и назначит встречу! 🔥

Обычно это занимает 10-30 минут.

Встретимся в удобном месте — ТЦ, метро, или где скажешь!

Погнали! 💨🇰🇿"""

        cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="❌ Отменить встречу",
                callback_data=f"cancel_meeting_{order_number}"
            )
        ]])

        await callback.message.edit_text(meeting_text, reply_markup=cancel_kb)
        await state.clear()
        await callback.answer()

        # Уведомление всем админам
        username = callback.from_user.username or callback.from_user.first_name
        for admin_id in config.ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🤝 <b>Новый заказ — встреча!</b>\n\n"
                    f"📦 #{order_number}\n"
                    f"👤 @{username} (ID: {callback.from_user.id})\n"
                    f"💵 Оплата: Наличными при встрече\n"
                    f"📍 Город: {city}\n"
                    f"💰 Сумма: {total}₸\n\n"
                    f"Свяжись с клиентом и назначь встречу!\n"
                    f"Завершить: /meeting_done {order_number}",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        
    except ValueError as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
        await state.clear()


@router.message(F.photo)
async def handle_payment_screenshot(message: Message):
    """Handle payment screenshot from customer."""
    # Forward to all admins
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=f"💳 Скриншот оплаты от @{message.from_user.username or message.from_user.id}\n\nПроверь и подтверди заказ командой /kaspi_paid"
            )
        except Exception:
            pass
    
    await message.answer(
        "✅ Скриншот получен, братан!\n\nАдмин проверит оплату в течение 5-15 минут 🔥"
    )


@router.callback_query(F.data.startswith("cancel_meeting_"))
async def cancel_meeting_callback(callback: CallbackQuery):
    """Allow user to cancel their pending meeting."""
    order_number = callback.data.replace("cancel_meeting_", "")
    db = get_db()

    # Получаем заказ
    order = await orders.get_order_by_number(db, order_number)
    if not order:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    # Проверяем что это заказ именно этого пользователя
    user = await users.get_user_by_telegram_id(db, callback.from_user.id)
    if not user or order['user_id'] != user['id']:
        await callback.answer("Это не твой заказ.", show_alert=True)
        return

    # Отменяем встречу
    cancelled = await cancel_meeting_by_order(db, order['id'])

    if cancelled:
        # Уведомляем админов
        for admin_id in config.ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"❌ Встреча отменена пользователем!\n\n"
                    f"🤝 Заказ #{order_number}\n"
                    f"👤 @{callback.from_user.username or callback.from_user.id}\n"
                    f"📱 ID: {callback.from_user.id}"
                )
            except Exception:
                pass

        await callback.message.edit_text(
            f"❌ Встреча по заказу #{order_number} отменена.\n\n"
            f"Если хочешь сделать новый заказ — /start"
        )
        await callback.answer("Встреча отменена ✅")
    else:
        await callback.answer(
            "Встречу уже нельзя отменить — она завершена или уже отменена.",
            show_alert=True
        )
