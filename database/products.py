"""Product database operations for SQLite."""
import aiosqlite
from typing import Optional, List


async def create_product(
    db: aiosqlite.Connection,
    name: str,
    price: int,
    flavors: List[str],
    stock_quantity: int
) -> int:
    """Create new product."""
    flavors_str = ','.join(flavors)
    cursor = await db.execute(
        """INSERT INTO products (name, price, flavors, stock_quantity)
           VALUES (?, ?, ?, ?)""",
        (name, price, flavors_str, stock_quantity)
    )
    lastrowid = cursor.lastrowid
    await cursor.close()
    await db.commit()
    return lastrowid


async def get_all_products(db: aiosqlite.Connection) -> List[dict]:
    """Get all products."""
    cursor = await db.execute("SELECT * FROM products ORDER BY id")
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


async def get_available_products(db: aiosqlite.Connection) -> List[dict]:
    """Get products with stock > 0."""
    cursor = await db.execute(
        "SELECT * FROM products WHERE stock_quantity > 0 ORDER BY id"
    )
    rows = await cursor.fetchall()
    await cursor.close()
    result = []
    for row in rows:
        product = dict(row)
        product['flavors'] = product['flavors'].split(',')
        result.append(product)
    return result


async def get_product_by_id(db: aiosqlite.Connection, product_id: int) -> Optional[dict]:
    """Get product by ID."""
    cursor = await db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row:
        product = dict(row)
        product['flavors'] = product['flavors'].split(',')
        return product
    return None


async def update_product(
    db: aiosqlite.Connection,
    product_id: int,
    **kwargs
) -> None:
    """Update product fields."""
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in ['price', 'stock_quantity']:
            updates.append(f"{key} = ?")
            values.append(value)
        elif key == 'flavors':
            updates.append("flavors = ?")
            values.append(','.join(value) if isinstance(value, list) else value)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, values)
        await db.commit()


async def delete_product(db: aiosqlite.Connection, product_id: int) -> None:
    """Delete product and clean up related records."""
    # Удаляем из корзин пользователей
    await db.execute("DELETE FROM cart_items WHERE product_id = ?", (product_id,))
    # Обнуляем ссылку в order_items чтобы не потерять историю заказов
    await db.execute(
        "UPDATE order_items SET product_id = NULL WHERE product_id = ?",
        (product_id,)
    )
    await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    await db.commit()


async def decrement_stock(db: aiosqlite.Connection, product_id: int, quantity: int) -> None:
    """Decrement product stock."""
    cursor = await db.execute(
        """UPDATE products 
           SET stock_quantity = stock_quantity - ?
           WHERE id = ? AND stock_quantity >= ?""",
        (quantity, product_id, quantity)
    )
    rowcount = cursor.rowcount
    await cursor.close()
    await db.commit()
    
    if rowcount == 0:
        raise ValueError("Insufficient stock")


async def get_low_stock_products(db: aiosqlite.Connection, threshold: int = 10) -> List[dict]:
    """Get products with stock below threshold."""
    cursor = await db.execute(
        "SELECT * FROM products WHERE stock_quantity < ? ORDER BY stock_quantity",
        (threshold,)
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]
