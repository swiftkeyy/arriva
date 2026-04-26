"""Admin inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Get admin dashboard keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="🔥 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🤝 Встречи", callback_data="admin_meetings")]
    ])


def get_order_actions_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Get order actions keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Kaspi оплачен", callback_data=f"confirm_kaspi_{order_number}")],
        [InlineKeyboardButton(text="🤝 Встреча завершена", callback_data=f"complete_meeting_{order_number}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_order_{order_number}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_orders")]
    ])
