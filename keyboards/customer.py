"""Customer inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Каталог", callback_data="view_catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")],
        [InlineKeyboardButton(text="💎 Реферальная программа", callback_data="view_referral")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])


def get_catalog_keyboard(products: List[dict]) -> InlineKeyboardMarkup:
    """Get catalog keyboard with product buttons."""
    buttons = []
    for product in products:
        buttons.append([InlineKeyboardButton(
            text=f"{product['name']} — {product['price']}₸",
            callback_data=f"product_{product['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_details_keyboard(product_id: int, flavors: List[str]) -> InlineKeyboardMarkup:
    """Get product details keyboard with flavor buttons."""
    buttons = []
    for flavor in flavors:
        buttons.append([InlineKeyboardButton(
            text=f"💨 {flavor}",
            callback_data=f"flavor_{product_id}_{flavor}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="view_catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quantity_keyboard(product_id: int, flavor: str) -> InlineKeyboardMarkup:
    """Get quantity selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data=f"qty_{product_id}_{flavor}_1"),
            InlineKeyboardButton(text="2", callback_data=f"qty_{product_id}_{flavor}_2"),
            InlineKeyboardButton(text="3", callback_data=f"qty_{product_id}_{flavor}_3")
        ],
        [
            InlineKeyboardButton(text="5", callback_data=f"qty_{product_id}_{flavor}_5"),
            InlineKeyboardButton(text="✏️ Другое", callback_data=f"qty_{product_id}_{flavor}_custom")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"product_{product_id}")]
    ])


def get_cart_keyboard(has_items: bool = True) -> InlineKeyboardMarkup:
    """Get cart keyboard."""
    buttons = []
    if has_items:
        buttons.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
        buttons.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад к каталогу", callback_data="view_catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_city_keyboard() -> InlineKeyboardMarkup:
    """Get city selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 Алматы", callback_data="city_Almaty")],
        [InlineKeyboardButton(text="🏙 Астана", callback_data="city_Astana")],
        [InlineKeyboardButton(text="🏙 Шымкент", callback_data="city_Shymkent")],
        [InlineKeyboardButton(text="🏙 Караганда", callback_data="city_Karaganda")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="view_cart")]
    ])


def get_payment_method_keyboard() -> InlineKeyboardMarkup:
    """Get payment method keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Kaspi", callback_data="payment_kaspi")],
        [InlineKeyboardButton(text="💵 Встреча (наличка)", callback_data="payment_meeting")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="view_cart")]
    ])
