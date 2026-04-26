"""Message formatters."""
from typing import List


def format_product_message(product: dict) -> str:
    """Format product details message."""
    flavors = ', '.join(product['flavors']) if isinstance(product['flavors'], list) else product['flavors']
    
    text = f"""🔥 {product['name']}

💰 Цена: {product['price']}₸
📦 В наличии: {product['stock_quantity']} шт
💨 Вкусы: {flavors}

Выбирай вкус, братан! Погнали! 🔥"""
    
    return text


def format_cart_message(cart_items: List[dict], total: int) -> str:
    """Format cart message."""
    if not cart_items:
        return "🛒 Корзина пустая, братан!\n\nПогнали добавлять что-то огненное! 💨"
    
    text = "🛒 ТВОЯ КОРЗИНА\n\n"
    
    for item in cart_items:
        text += f"💨 {item['product_name']} — {item['flavor']}\n"
        text += f"   {item['quantity']} шт × {item['unit_price']}₸ = {item['subtotal']}₸\n\n"
    
    text += f"💰 ИТОГО: {total}₸\n\nПогнали оформлять, братан! 🔥"
    
    return text


def format_order_message(order: dict) -> str:
    """Format order details message."""
    text = f"""📦 ЗАКАЗ #{order['order_number']}

👤 Клиент: @{order['username'] or 'Unknown'}
💰 Сумма: {order['total_amount']}₸
📍 Город: {order['delivery_city']}
🏠 Адрес: {order['delivery_address']}
💳 Оплата: {order['payment_method']}
📊 Статус: {order['status']}

🛍 ТОВАРЫ:
"""
    
    for item in order.get('items', []):
        text += f"• {item['product_name']} — {item['flavor']} ({item['quantity']} шт)\n"
    
    return text


def format_referral_stats_message(stats: dict) -> str:
    """Format referral statistics message."""
    text = f"""💎 ТВОЯ РЕФЕРАЛЬНАЯ СТАТИСТИКА

👥 Приглашено друзей: {stats['referee_count']}
💰 Заработано: {stats['total_bonuses']}₸

Погнали зарабатывать больше, братан! 🔥"""
    
    return text


def apply_brand_voice(message: str) -> str:
    """Apply brand voice to message."""
    # Add emojis if not present
    if '🔥' not in message and '💨' not in message:
        message += " 🔥"
    
    return message
