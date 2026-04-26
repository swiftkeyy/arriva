"""Admin command handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import orders, products, users
from keyboards.admin import get_admin_dashboard_keyboard, get_order_actions_keyboard
from database.db_instance import get_db
import config

router = Router()


class AddProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_flavors = State()
    waiting_for_stock = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Show admin dashboard."""
    db = get_db()
    
    # Get today's stats
    pending_orders = await orders.get_orders_by_status(db, 'pending')
    low_stock = await products.get_low_stock_products(db)
    
    text = f"""📊 ARRIVA KZ v4.0 — ADMIN DASHBOARD

📦 Новых заказов: {len(pending_orders)}
⚠️ Товаров с низким остатком: {len(low_stock)}

Выбери действие, братан! 🔥"""
    
    await message.answer(text, reply_markup=get_admin_dashboard_keyboard())


@router.callback_query(F.data == "admin_products")
async def show_products_callback(callback: CallbackQuery):
    """Show products via callback."""
    db = get_db()
    all_products = await products.get_all_products(db)
    
    if not all_products:
        text = "🔥 Нет товаров в базе"
    else:
        text = "🔥 ТОВАРЫ:\n\n"
        for product in all_products:
            flavors = product['flavors'].split(',') if isinstance(product['flavors'], str) else product['flavors']
            text += f"📦 {product['name']}\n"
            text += f"💰 {product['price']}₸\n"
            text += f"📊 Остаток: {product['stock_quantity']} шт\n"
            text += f"💨 Вкусы: {', '.join(flavors[:3])}\n\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_stats_callback(callback: CallbackQuery):
    """Show stats via callback."""
    db = get_db()
    
    # Get orders stats
    cursor = await db.execute(
        """SELECT 
               COUNT(*) as total_orders,
               SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as total_revenue,
               AVG(CASE WHEN status = 'completed' THEN total_amount ELSE NULL END) as avg_order
           FROM orders
           WHERE DATE(created_at) = DATE('now')"""
    )
    today = await cursor.fetchone()
    await cursor.close()
    
    cursor = await db.execute(
        """SELECT 
               COUNT(*) as total_orders,
               SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as total_revenue
           FROM orders
           WHERE DATE(created_at) >= DATE('now', '-7 days')"""
    )
    week = await cursor.fetchone()
    await cursor.close()
    
    text = f"""📊 СТАТИСТИКА ARRIVA KZ

📅 СЕГОДНЯ:
📦 Заказов: {today[0]}
💰 Выручка: {today[1] or 0}₸
📈 Средний чек: {int(today[2]) if today[2] else 0}₸

📅 ЗА НЕДЕЛЮ:
📦 Заказов: {week[0]}
💰 Выручка: {week[1] or 0}₸"""
    
    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def show_broadcast_callback(callback: CallbackQuery):
    """Show broadcast menu via callback."""
    text = """📢 РАССЫЛКА

Используй команду /broadcast для создания рассылки

Доступные шаблоны:
• Новинки недели
• Флеш-скидка
• Реферальная акция
• Напоминание о корзине
• И другие..."""
    
    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_meetings")
async def show_meetings_callback(callback: CallbackQuery):
    """Show meetings via callback."""
    db = get_db()
    
    from database.meetings import get_meetings_by_status
    
    pending = await get_meetings_by_status(db, 'pending')
    
    if not pending:
        text = "📅 Нет запланированных встреч"
    else:
        text = "📅 ЗАПЛАНИРОВАННЫЕ ВСТРЕЧИ:\n\n"
        for meeting in pending[:10]:
            text += f"🤝 Заказ #{meeting['order_number']}\n"
            text += f"👤 @{meeting['username'] or 'Unknown'}\n"
            text += f"📱 ID: {meeting['telegram_id']}\n\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
@router.message(Command("orders"))
async def show_orders(event):
    """Show orders list."""
    if isinstance(event, CallbackQuery):
        message = event.message
        db = get_db()
    else:
        message = event
        db = get_db()
    
    pending = await orders.get_orders_by_status(db, 'pending')
    
    if not pending:
        text = "📦 Нет новых заказов"
    else:
        text = "📦 НОВЫЕ ЗАКАЗЫ:\n\n"
        for order in pending[:10]:
            text += f"#{order['order_number']}\n"
            text += f"👤 @{order['username'] or 'Unknown'}\n"
            text += f"💰 {order['total_amount']}₸\n"
            text += f"📍 {order['delivery_city']}\n"
            text += f"💳 {order['payment_method']}\n\n"
    
    if isinstance(event, CallbackQuery):
        await message.edit_text(text, reply_markup=get_admin_dashboard_keyboard())
        await event.answer()
    else:
        await message.answer(text)


@router.message(Command("kaspi_paid"))
async def cmd_kaspi_paid(message: Message):
    """Mark Kaspi payment as confirmed."""
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /kaspi_paid ORD-...")
        return
    
    order_number = parts[1]
    db = get_db()
    
    order = await orders.get_order_by_number(db, order_number)
    if not order:
        await message.answer("Заказ не найден")
        return
    
    await orders.update_order_status(db, order_number, 'confirmed')
    
    # Notify customer
    try:
        await message.bot.send_message(
            order['telegram_id'],
            f"""✅ Оплата подтверждена!

Заказ #{order_number}
💰 {order['total_amount']}₸

🚚 Доставка: 2 часа (Алматы/Астана)

Погнали, братан! 🔥"""
        )
    except Exception:
        pass
    
    await message.answer(f"✅ Заказ #{order_number} подтверждён!")


@router.message(Command("meeting_done"))
async def cmd_meeting_done(message: Message):
    """Mark meeting as completed."""
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /meeting_done ORD-...")
        return
    
    order_number = parts[1]
    db = get_db()
    
    order = await orders.get_order_by_number(db, order_number)
    if not order:
        await message.answer("Заказ не найден")
        return
    
    await orders.update_order_status(db, order_number, 'completed')
    
    # Update user total spent
    await users.update_user_total_spent(db, order['user_id'], order['total_amount'])
    
    # Check and process referral bonus
    from database.referrals import process_referral_bonus
    try:
        await process_referral_bonus(db, order['user_id'], order['id'])
    except Exception:
        pass
    
    # Notify customer
    try:
        await message.bot.send_message(
            order['telegram_id'],
            f"""🔥 Спасибо за покупку, братан!

Заказ #{order_number} завершён!

+150 Arriva Points на твой счёт
Приведи друга и получи 500₸ кэшбэк

Погнали дальше! 💎🇰🇿"""
        )
    except Exception:
        pass
    
    await message.answer(f"✅ Встреча #{order_number} завершена!")


@router.message(Command("lowstock"))
async def cmd_lowstock(message: Message):
    """Show low stock products."""
    db = get_db()
    low_stock = await products.get_low_stock_products(db)
    
    if not low_stock:
        await message.answer("✅ Все товары в наличии!")
        return
    
    text = "⚠️ НИЗКИЙ ОСТАТОК:\n\n"
    for product in low_stock:
        text += f"🔥 {product['name']}\n"
        text += f"   Остаток: {product['stock_quantity']} шт\n\n"
    
    await message.answer(text)



@router.message(Command("addproduct"))
async def cmd_addproduct(message: Message, state: FSMContext):
    """Start adding new product."""
    await state.set_state(AddProductStates.waiting_for_name)
    await message.answer("Введи название товара, братан:")


@router.message(AddProductStates.waiting_for_name)
async def process_product_name(message: Message, state: FSMContext):
    """Process product name."""
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("Введи цену в тенге (например: 1899):")


@router.message(AddProductStates.waiting_for_price)
async def process_product_price(message: Message, state: FSMContext):
    """Process product price."""
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("Братан, введи нормальную цену! Только цифры больше 0:")
        return
    
    await state.update_data(price=price)
    await state.set_state(AddProductStates.waiting_for_flavors)
    await message.answer("Введи вкусы через запятую (например: Mango Ice, Strawberry, Blue Razz):")


@router.message(AddProductStates.waiting_for_flavors)
async def process_product_flavors(message: Message, state: FSMContext):
    """Process product flavors."""
    flavors = [f.strip() for f in message.text.split(',')]
    if not flavors:
        await message.answer("Братан, введи хотя бы один вкус!")
        return
    
    await state.update_data(flavors=flavors)
    await state.set_state(AddProductStates.waiting_for_stock)
    await message.answer("Введи количество на складе:")


@router.message(AddProductStates.waiting_for_stock)
async def process_product_stock(message: Message, state: FSMContext):
    """Process product stock and create product."""
    try:
        stock = int(message.text)
        if stock < 0:
            raise ValueError()
    except ValueError:
        await message.answer("Братан, введи нормальное количество! Только цифры от 0:")
        return
    
    data = await state.get_data()
    db = get_db()
    
    product_id = await products.create_product(
        db,
        data['name'],
        data['price'],
        data['flavors'],
        stock
    )
    
    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"🔥 {data['name']}\n"
        f"💰 {data['price']}₸\n"
        f"💨 Вкусы: {', '.join(data['flavors'])}\n"
        f"📦 Остаток: {stock} шт"
    )
    
    await state.clear()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show statistics."""
    db = get_db()
    
    # Get orders stats
    cursor = await db.execute(
        """SELECT 
               COUNT(*) as total_orders,
               SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as total_revenue,
               AVG(CASE WHEN status = 'completed' THEN total_amount ELSE NULL END) as avg_order
           FROM orders
           WHERE DATE(created_at) = DATE('now')"""
    )
    today = await cursor.fetchone()
    
    cursor = await db.execute(
        """SELECT 
               COUNT(*) as total_orders,
               SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as total_revenue
           FROM orders
           WHERE DATE(created_at) >= DATE('now', '-7 days')"""
    )
    week = await cursor.fetchone()
    
    cursor = await db.execute(
        """SELECT 
               COUNT(*) as total_orders,
               SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END) as total_revenue
           FROM orders
           WHERE DATE(created_at) >= DATE('now', '-30 days')"""
    )
    month = await cursor.fetchone()
    
    # Get top products
    cursor = await db.execute(
        """SELECT p.name, SUM(oi.quantity) as total_sold
           FROM order_items oi
           JOIN products p ON oi.product_id = p.id
           JOIN orders o ON oi.order_id = o.id
           WHERE o.status = 'completed' AND DATE(o.created_at) >= DATE('now', '-7 days')
           GROUP BY p.name
           ORDER BY total_sold DESC
           LIMIT 5"""
    )
    top_products = await cursor.fetchall()
    
    # Get city stats
    cursor = await db.execute(
        """SELECT delivery_city, COUNT(*) as order_count, SUM(total_amount) as revenue
           FROM orders
           WHERE status = 'completed'
           GROUP BY delivery_city
           ORDER BY revenue DESC"""
    )
    cities = await cursor.fetchall()
    
    # Get conversion rate
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    total_users = (await cursor.fetchone())[0]
    
    cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM orders WHERE status = 'completed'")
    converted_users = (await cursor.fetchone())[0]
    
    conversion = (converted_users / total_users * 100) if total_users > 0 else 0
    
    text = f"""📊 СТАТИСТИКА ARRIVA KZ

📅 СЕГОДНЯ:
📦 Заказов: {today[0]}
💰 Выручка: {today[1] or 0}₸
📈 Средний чек: {int(today[2]) if today[2] else 0}₸

📅 ЗА НЕДЕЛЮ:
📦 Заказов: {week[0]}
💰 Выручка: {week[1] or 0}₸

📅 ЗА МЕСЯЦ:
📦 Заказов: {month[0]}
💰 Выручка: {month[1] or 0}₸

🔥 ТОП-5 ТОВАРОВ (неделя):
"""
    
    for i, product in enumerate(top_products, 1):
        text += f"{i}. {product[0]} — {product[1]} шт\n"
    
    text += f"\n🏙 ПО ГОРОДАМ:\n"
    for city in cities:
        text += f"{city[0]}: {city[1]} заказов, {city[2]}₸\n"
    
    text += f"\n📊 Конверсия: {conversion:.1f}%"
    
    await message.answer(text)


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Show top products."""
    db = get_db()
    
    cursor = await db.execute(
        """SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.subtotal) as revenue
           FROM order_items oi
           JOIN products p ON oi.product_id = p.id
           JOIN orders o ON oi.order_id = o.id
           WHERE o.status = 'completed' AND DATE(o.created_at) >= DATE('now', '-7 days')
           GROUP BY p.name
           ORDER BY total_sold DESC
           LIMIT 10"""
    )
    products_week = await cursor.fetchall()
    
    text = "🔥 ТОП-10 ТОВАРОВ ЗА НЕДЕЛЮ:\n\n"
    
    for i, product in enumerate(products_week, 1):
        text += f"{i}. {product[0]}\n"
        text += f"   Продано: {product[1]} шт | Выручка: {product[2]}₸\n\n"
    
    if not products_week:
        text = "Пока нет продаж за неделю"
    
    await message.answer(text)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Show settings."""
    db = get_db()
    
    cursor = await db.execute("SELECT key, value FROM settings")
    settings = await cursor.fetchall()
    
    text = "⚙️ НАСТРОЙКИ МАГАЗИНА:\n\n"
    
    for setting in settings:
        text += f"🔹 {setting[0]}: {setting[1]}\n"
    
    await message.answer(text)


@router.message(Command("meetings"))
async def cmd_meetings(message: Message):
    """Show meetings."""
    db = get_db()
    
    from database.meetings import get_meetings_by_status
    
    pending = await get_meetings_by_status(db, 'pending')
    
    if not pending:
        await message.answer("📅 Нет запланированных встреч")
        return
    
    text = "📅 ЗАПЛАНИРОВАННЫЕ ВСТРЕЧИ:\n\n"
    
    for meeting in pending:
        text += f"🤝 Заказ #{meeting['order_number']}\n"
        text += f"👤 @{meeting['username'] or 'Unknown'}\n"
        text += f"📱 ID: {meeting['telegram_id']}\n\n"
    
    await message.answer(text)


@router.message(Command("referrals"))
async def cmd_referrals(message: Message):
    """Show referral statistics."""
    db = get_db()
    
    from database.referrals import get_all_referral_stats
    
    stats = await get_all_referral_stats(db)
    
    if not stats:
        await message.answer("💎 Пока нет рефералов")
        return
    
    text = "💎 СТАТИСТИКА РЕФЕРАЛОВ:\n\n"
    
    for i, user in enumerate(stats[:20], 1):
        text += f"{i}. @{user['username'] or user['telegram_id']}\n"
        text += f"   Приглашено: {user['referee_count']} | Заработано: {user['total_bonuses']}₸\n\n"
    
    await message.answer(text)
