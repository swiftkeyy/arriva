"""Input validators."""
from typing import Optional


def validate_quantity(quantity: str) -> Optional[int]:
    """Validate quantity input."""
    try:
        qty = int(quantity)
        if 1 <= qty <= 10:
            return qty
        return None
    except ValueError:
        return None


def validate_price(price: str) -> Optional[int]:
    """Validate price input."""
    try:
        p = int(price)
        if p > 0:
            return p
        return None
    except ValueError:
        return None


def validate_telegram_id(telegram_id: str) -> Optional[int]:
    """Validate Telegram ID."""
    try:
        tid = int(telegram_id)
        if tid > 0:
            return tid
        return None
    except ValueError:
        return None


def validate_order_number(order_number: str) -> bool:
    """Validate order number format."""
    return order_number.startswith("ORD-") and len(order_number) > 10


def validate_address(address: str) -> bool:
    """Validate delivery address."""
    return len(address.strip()) >= 10
