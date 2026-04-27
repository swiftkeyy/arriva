"""Database connection management for SQLite."""
import aiosqlite
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_db: Optional[aiosqlite.Connection] = None


async def init_db(database_path: str) -> aiosqlite.Connection:
    """Initialize database connection."""
    global _db
    try:
        # Create data directory if it doesn't exist
        import os
        db_dir = os.path.dirname(database_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created directory: {db_dir}")
        
        _db = await aiosqlite.connect(database_path)
        _db.row_factory = aiosqlite.Row
        logger.info(f"Database connection initialized: {database_path}")
        
        # Enable foreign keys
        await _db.execute("PRAGMA foreign_keys = ON")
        await _db.commit()
        
        # Create tables
        await create_tables(_db)
        
        # Apply migrations for existing databases
        await run_migrations(_db)
        
        # Test connection
        await _db.execute("SELECT 1")
        logger.info("Database connection test successful")
        
        return _db
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def create_tables(db: aiosqlite.Connection):
    """Create database tables."""
    schema = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        referral_code TEXT UNIQUE NOT NULL,
        referred_by_id INTEGER,
        total_spent INTEGER DEFAULT 0,
        is_vip INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referred_by_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);

    -- Products table
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        flavors TEXT NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Product flavor stock table
    CREATE TABLE IF NOT EXISTS product_flavor_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        flavor TEXT NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        UNIQUE(product_id, flavor),
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    -- Orders table
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount INTEGER NOT NULL,
        delivery_city TEXT NOT NULL,
        delivery_address TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmed_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

    -- Order items table
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        flavor TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        subtotal INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    -- Referral bonuses table
    CREATE TABLE IF NOT EXISTS referral_bonuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER NOT NULL,
        referee_id INTEGER NOT NULL,
        order_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users(id),
        FOREIGN KEY (referee_id) REFERENCES users(id),
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );

    CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_id ON referral_bonuses(referrer_id);

    -- Meetings table
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        scheduled_time TIMESTAMP,
        location TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
    CREATE INDEX IF NOT EXISTS idx_meetings_scheduled_time ON meetings(scheduled_time);

    -- Cart items table
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        flavor TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);

    -- Broadcasts table
    CREATE TABLE IF NOT EXISTS broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        template_name TEXT NOT NULL,
        message_text TEXT NOT NULL,
        target_audience TEXT NOT NULL,
        total_sent INTEGER DEFAULT 0,
        total_failed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- System settings table
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    await db.executescript(schema)
    await db.commit()
    
    # Insert default products
    cursor = await db.execute("SELECT COUNT(*) FROM products")
    count = (await cursor.fetchone())[0]
    await cursor.close()
    
    if count == 0:
        products = [
            ('Arriva Pro 8000', 1899, 'Mango Ice,Strawberry Kiwi,Blue Razz,Cola Energy', 50),
            ('Elf Bar BC5000', 1699, 'Mango,Watermelon,Grape,Mint', 45),
            ('Crystal Bar 6000', 1599, 'Lemon Mint,Blueberry,Peach', 40),
            ('Geek Bar Pulse 6000', 1999, 'Watermelon Ice,Strawberry Banana,Miami Mint', 35),
            ('Arriva Max 12000', 2499, 'Almaty Cherry,Shymkent Lemon,Kazakh Energy', 30),
            ('Vozol Star 8000', 1799, 'Cola,Energy Drink,Pineapple', 25),
            ('Waka 6000', 1499, 'Mango Lassi,Passion Fruit', 20),
            ('Arriva Black Edition 5000', 1399, 'Tobacco,Coffee,Mint', 15),
            ('Arriva Desert 7000', 2099, 'Tiramisu,Cheesecake,Chocolate', 12),
            ('Crystal Legend 8000', 2199, 'Sakura,Lychee,Dragon Fruit', 10),
            ('Elf Bar Ultra 9000', 2299, 'Red Bull,Monster,7Up', 8),
            ('Arriva Limited 10000', 2699, 'Алматы Sunset', 5)
        ]
        
        await db.executemany(
            "INSERT INTO products (name, price, flavors, stock_quantity) VALUES (?, ?, ?, ?)",
            products
        )
        await db.commit()
        logger.info("Default products inserted")
    
    # Insert default settings
    cursor = await db.execute("SELECT COUNT(*) FROM settings")
    count = (await cursor.fetchone())[0]
    await cursor.close()
    
    if count == 0:
        settings = [
            ('shop_name', 'Arriva Shop KZ v4.0'),
            ('kaspi_account', '+7 777 123 4567'),
            ('kaspi_recipient', 'Arriva Shop KZ'),
            ('delivery_cities', 'Almaty,Astana,Shymkent,Karaganda'),
            ('min_order_amount', '1000'),
            ('referral_bonus_amount', '500')
        ]
        
        await db.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            settings
        )
        await db.commit()
        logger.info("Default settings inserted")


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Apply schema migrations for existing databases."""
    # Migration 1: allow product_id to be NULL in order_items
    try:
        cursor = await db.execute("PRAGMA table_info(order_items)")
        columns = await cursor.fetchall()
        await cursor.close()
        product_id_col = next((c for c in columns if c[1] == "product_id"), None)
        if product_id_col and product_id_col[3] == 1:
            logger.info("Migrating order_items: making product_id nullable...")
            await db.executescript("""
                PRAGMA foreign_keys = OFF;
                BEGIN TRANSACTION;
                CREATE TABLE IF NOT EXISTS order_items_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER,
                    product_name TEXT NOT NULL,
                    flavor TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    subtotal INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
                INSERT INTO order_items_new SELECT * FROM order_items;
                DROP TABLE order_items;
                ALTER TABLE order_items_new RENAME TO order_items;
                COMMIT;
                PRAGMA foreign_keys = ON;
            """)
            logger.info("Migration 1 complete: order_items.product_id is now nullable")
    except Exception as e:
        logger.error(f"Migration 1 failed: {e}")

    # Migration 2: create product_flavor_stock and populate from existing products
    try:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='product_flavor_stock'"
        )
        exists = await cursor.fetchone()
        await cursor.close()
        if not exists:
            logger.info("Migration 2: creating product_flavor_stock table...")
            await db.execute("""
                CREATE TABLE product_flavor_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    flavor TEXT NOT NULL,
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(product_id, flavor),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)
            # Populate from existing products — делим stock_quantity поровну между вкусами
            cursor = await db.execute("SELECT id, flavors, stock_quantity FROM products")
            rows = await cursor.fetchall()
            await cursor.close()
            for row in rows:
                product_id, flavors_str, total_stock = row[0], row[1], row[2]
                flavor_list = [f.strip() for f in flavors_str.split(',') if f.strip()]
                if not flavor_list:
                    continue
                per_flavor = max(1, total_stock // len(flavor_list))
                for flavor in flavor_list:
                    await db.execute(
                        "INSERT OR IGNORE INTO product_flavor_stock (product_id, flavor, stock_quantity) VALUES (?, ?, ?)",
                        (product_id, flavor, per_flavor)
                    )
            await db.commit()
            logger.info("Migration 2 complete: product_flavor_stock populated")
    except Exception as e:
        logger.error(f"Migration 2 failed: {e}")


async def close_db():
    """Close database connection."""
    global _db
    if _db:
        await _db.close()
        logger.info("Database connection closed")
        _db = None


def get_db() -> aiosqlite.Connection:
    """Get current database connection."""
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


async def health_check() -> bool:
    """Check database connectivity."""
    try:
        db = get_db()
        await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
