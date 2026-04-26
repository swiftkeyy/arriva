"""Admin inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Get admin dashboard keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="🔥 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🤝 Встречи", callback_data="admin_meetings")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="💎 Рефералы", callback_data="admin_referrals")],
        [InlineKeyboardButton(text="🏙 Города", callback_data="admin_cities")]
    ])


def get_products_menu_keyboard() -> InlineKeyboardMarkup:
    """Get products management menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список товаров", callback_data="products_list")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="products_add")],
        [InlineKeyboardButton(text="⚠️ Низкий остаток", callback_data="products_lowstock")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_products_list_keyboard(products: list) -> InlineKeyboardMarkup:
    """Get products list with action buttons."""
    buttons = []
    
    for product in products[:20]:  # Show up to 20
        status = "✅" if product['stock_quantity'] > 10 else "⚠️" if product['stock_quantity'] > 0 else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {product['name']} ({product['stock_quantity']} шт)",
                callback_data=f"product_manage_{product['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_products")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_manage_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Get product management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"product_price_{product_id}")],
        [InlineKeyboardButton(text="📦 Добавить остаток", callback_data=f"product_stock_{product_id}")],
        [InlineKeyboardButton(text="💨 Изменить вкусы", callback_data=f"product_flavors_{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"product_delete_{product_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="products_list")]
    ])


def get_broadcast_menu_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Всем пользователям", callback_data="broadcast_all")],
        [InlineKeyboardButton(text="⭐️ VIP пользователям", callback_data="broadcast_vip")],
        [InlineKeyboardButton(text="🏙 По городу", callback_data="broadcast_city")],
        [InlineKeyboardButton(text="🛒 С брошенной корзиной", callback_data="broadcast_cart")],
        [InlineKeyboardButton(text="📋 Шаблоны", callback_data="broadcast_templates")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_broadcast_templates_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast templates."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Новинки недели", callback_data="template_new_arrivals")],
        [InlineKeyboardButton(text="⚡️ Флеш-скидка", callback_data="template_flash_sale")],
        [InlineKeyboardButton(text="💎 Реферальная акция", callback_data="template_referral")],
        [InlineKeyboardButton(text="🛒 Напоминание о корзине", callback_data="template_cart_reminder")],
        [InlineKeyboardButton(text="☀️ Утренний вайб", callback_data="template_morning")],
        [InlineKeyboardButton(text="🎁 После покупки", callback_data="template_post_purchase")],
        [InlineKeyboardButton(text="⭐️ VIP предложение", callback_data="template_vip")],
        [InlineKeyboardButton(text="⚠️ Низкий остаток", callback_data="template_low_stock")],
        [InlineKeyboardButton(text="🎉 Праздничная акция", callback_data="template_holiday")],
        [InlineKeyboardButton(text="🔄 Реактивация", callback_data="template_reactivation")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast")]
    ])


def get_users_menu_keyboard() -> InlineKeyboardMarkup:
    """Get users management menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="users_all")],
        [InlineKeyboardButton(text="⭐️ VIP пользователи", callback_data="users_vip")],
        [InlineKeyboardButton(text="🚫 Заблокированные", callback_data="users_blocked")],
        [InlineKeyboardButton(text="🔍 Поиск по ID", callback_data="users_search")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    """Get statistics menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today")],
        [InlineKeyboardButton(text="📅 За неделю", callback_data="stats_week")],
        [InlineKeyboardButton(text="📅 За месяц", callback_data="stats_month")],
        [InlineKeyboardButton(text="🔥 Топ товары", callback_data="stats_top_products")],
        [InlineKeyboardButton(text="🏙 По городам", callback_data="stats_cities")],
        [InlineKeyboardButton(text="📊 Конверсия", callback_data="stats_conversion")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_orders_menu_keyboard() -> InlineKeyboardMarkup:
    """Get orders menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Новые", callback_data="orders_pending")],
        [InlineKeyboardButton(text="✅ Подтверждённые", callback_data="orders_confirmed")],
        [InlineKeyboardButton(text="✔️ Завершённые", callback_data="orders_completed")],
        [InlineKeyboardButton(text="❌ Отменённые", callback_data="orders_cancelled")],
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="orders_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_order_actions_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Get order actions keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Kaspi оплачен", callback_data=f"confirm_kaspi_{order_number}")],
        [InlineKeyboardButton(text="🤝 Встреча завершена", callback_data=f"complete_meeting_{order_number}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_number}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_orders")]
    ])


def get_back_to_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Get back to dashboard button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="admin_dashboard")]
    ])


def get_cities_menu_keyboard() -> InlineKeyboardMarkup:
    """Get cities management menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список городов", callback_data="cities_list")],
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="cities_add")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_dashboard")]
    ])


def get_cities_list_keyboard(cities: list) -> InlineKeyboardMarkup:
    """Get cities list with delete buttons."""
    buttons = []
    
    for city in cities:
        buttons.append([
            InlineKeyboardButton(
                text=f"🏙 {city}",
                callback_data=f"city_info_{city}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"city_delete_{city}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_cities")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

