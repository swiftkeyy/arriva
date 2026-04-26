"""Cart database operations for SQLite."""
import aiosqlite
from typing import List


async def add_to_cart(
    db: aiosqlite.Connection,
    user_id: int,
    product_id: int,
    flavor: str,
    quantity: int
):
    """Add item to cart."""
    # Check if item already in cart
    cursor = await db.execute(
        """SELECT id, quantity FROM cart_items 
           WHERE user_id = ? AND product_id = ? AND flavor = ?""",
        (user_id, product_id, flavor)
    )
    existing = await cursor.fetchone()
    
    if existing:
        # Update quantity
        await db.execute(
            "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing[0])
        )
    else:
        # Insert new item
        await db.execute(
            """INSERT INTO cart_items (user_id, product_id, flavor, quantity)
               VALUES (?, ?, ?, ?)""",
            (user_id, product_id, flavor, quantity)
        )
    
    await db.commit()


async def get_user_cart(db: aiosqlite.Connection, user_id: int) -> List[dict]:
    """Get user's cart items with product details."""
    cursor = await db.execute(
        """SELECT c.id, c.product_id, c.flavor, c.quantity,
                  p.name as product_name, p.price as unit_price,
                  (p.price * c.quantity) as subtotal
           FROM cart_items c
           JOIN products p ON c.product_id = p.id
           WHERE c.user_id = ?""",
        (user_id,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def remove_from_cart(db: aiosqlite.Connection, cart_item_id: int):
    """Remove item from cart."""
    await db.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
    await db.commit()


async def clear_cart(db: aiosqlite.Connection, user_id: int):
    """Clear user's cart."""
    await db.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    await db.commit()


async def get_cart_total(db: aiosqlite.Connection, user_id: int) -> int:
    """Get cart total amount."""
    cursor = await db.execute(
        """SELECT COALESCE(SUM(p.price * c.quantity), 0)
           FROM cart_items c
           JOIN products p ON c.product_id = p.id
           WHERE c.user_id = ?""",
        (user_id,)
    )
    row = await cursor.fetchone()
    return row[0] if row else 0
