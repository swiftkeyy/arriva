"""Order database operations for SQLite."""
import aiosqlite
from typing import List, Optional
from datetime import datetime
import random
import string


def generate_order_number() -> str:
    """Generate unique order number."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"ORD-{timestamp}-{random_part}"


async def create_order(
    db: aiosqlite.Connection,
    user_id: int,
    cart_items: List[dict],
    delivery_city: str,
    delivery_address: str,
    payment_method: str
) -> str:
    """Create order with transaction."""
    order_number = generate_order_number()
    total_amount = sum(item['subtotal'] for item in cart_items)
    
    # Create order
    cursor = await db.execute(
        """INSERT INTO orders (order_number, user_id, total_amount, delivery_city, 
                              delivery_address, payment_method, status)
           VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
        (order_number, user_id, total_amount, delivery_city, delivery_address, payment_method)
    )
    order_id = cursor.lastrowid
    await cursor.close()
    
    # Insert order items and decrement stock
    for item in cart_items:
        await db.execute(
            """INSERT INTO order_items (order_id, product_id, product_name, flavor, 
                                        quantity, unit_price, subtotal)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item['product_id'], item['product_name'], item['flavor'],
             item['quantity'], item['unit_price'], item['subtotal'])
        )

        # Decrement flavor stock first, fallback to general stock
        cursor = await db.execute(
            """UPDATE product_flavor_stock
               SET stock_quantity = stock_quantity - ?
               WHERE product_id = ? AND flavor = ? AND stock_quantity >= ?""",
            (item['quantity'], item['product_id'], item['flavor'], item['quantity'])
        )
        rowcount = cursor.rowcount
        await cursor.close()

        if rowcount == 0:
            # Fallback: general stock
            cursor = await db.execute(
                """UPDATE products
                   SET stock_quantity = stock_quantity - ?
                   WHERE id = ? AND stock_quantity >= ?""",
                (item['quantity'], item['product_id'], item['quantity'])
            )
            rowcount = cursor.rowcount
            await cursor.close()
            if rowcount == 0:
                raise ValueError(f"Insufficient stock for product {item['product_name']}")
        else:
            # Sync general stock
            cursor = await db.execute(
                "SELECT COALESCE(SUM(stock_quantity),0) FROM product_flavor_stock WHERE product_id = ?",
                (item['product_id'],)
            )
            total = (await cursor.fetchone())[0]
            await cursor.close()
            await db.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (total, item['product_id']))
    
    # Clear cart
    await db.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    await db.commit()
    
    return order_number


async def get_order_by_number(db: aiosqlite.Connection, order_number: str) -> Optional[dict]:
    """Get order by number with items."""
    cursor = await db.execute(
        """SELECT o.*, u.telegram_id, u.username
           FROM orders o
           JOIN users u ON o.user_id = u.id
           WHERE o.order_number = ?""",
        (order_number,)
    )
    order = await cursor.fetchone()
    await cursor.close()
    
    if not order:
        return None
    
    cursor = await db.execute(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order['id'],)
    )
    items = await cursor.fetchall()
    await cursor.close()
    
    return {
        **dict(order),
        'items': [dict(item) for item in items]
    }


async def get_orders_by_status(db: aiosqlite.Connection, status: str) -> List[dict]:
    """Get orders by status."""
    cursor = await db.execute(
        """SELECT o.*, u.username
           FROM orders o
           JOIN users u ON o.user_id = u.id
           WHERE o.status = ?
           ORDER BY o.created_at DESC""",
        (status,)
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


async def update_order_status(db: aiosqlite.Connection, order_number: str, status: str):
    """Update order status."""
    timestamp_field = None
    if status == 'confirmed':
        timestamp_field = 'confirmed_at'
    elif status == 'completed':
        timestamp_field = 'completed_at'
    
    if timestamp_field:
        await db.execute(
            f"""UPDATE orders 
                SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP
                WHERE order_number = ?""",
            (status, order_number)
        )
    else:
        await db.execute(
            "UPDATE orders SET status = ? WHERE order_number = ?",
            (status, order_number)
        )
    
    await db.commit()


async def cancel_order(db: aiosqlite.Connection, order_number: str):
    """Cancel order and restore stock."""
    # Get order items
    cursor = await db.execute(
        "SELECT id FROM orders WHERE order_number = ?",
        (order_number,)
    )
    order = await cursor.fetchone()
    await cursor.close()
    
    if not order:
        return
    
    cursor = await db.execute(
        "SELECT product_id, flavor, quantity FROM order_items WHERE order_id = ?",
        (order['id'],)
    )
    items = await cursor.fetchall()
    await cursor.close()

    # Restore flavor stock
    for item in items:
        if item['product_id']:
            await db.execute(
                """INSERT INTO product_flavor_stock (product_id, flavor, stock_quantity)
                   VALUES (?, ?, ?)
                   ON CONFLICT(product_id, flavor) DO UPDATE SET stock_quantity = stock_quantity + ?""",
                (item['product_id'], item['flavor'], item['quantity'], item['quantity'])
            )
            cursor = await db.execute(
                "SELECT COALESCE(SUM(stock_quantity),0) FROM product_flavor_stock WHERE product_id = ?",
                (item['product_id'],)
            )
            total = (await cursor.fetchone())[0]
            await cursor.close()
            await db.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (total, item['product_id']))
    
    # Update order status
    await db.execute(
        "UPDATE orders SET status = 'cancelled' WHERE order_number = ?",
        (order_number,)
    )
    
    await db.commit()
