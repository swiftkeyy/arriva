"""User database operations for SQLite."""
import aiosqlite
import random
import string
from typing import Optional


def generate_referral_code() -> str:
    """Generate unique referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


async def create_user(
    db: aiosqlite.Connection,
    telegram_id: int,
    username: Optional[str],
    referred_by_code: Optional[str] = None
) -> int:
    """Create new user with optional referral."""
    referral_code = generate_referral_code()
    
    # Check if referral code exists
    referred_by_id = None
    if referred_by_code:
        cursor = await db.execute(
            "SELECT id FROM users WHERE referral_code = ?",
            (referred_by_code,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row:
            referred_by_id = row[0]
    
    # Create user
    cursor = await db.execute(
        """INSERT INTO users (telegram_id, username, referral_code, referred_by_id)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(telegram_id) DO UPDATE SET username = ?
           RETURNING id""",
        (telegram_id, username, referral_code, referred_by_id, username)
    )
    row = await cursor.fetchone()
    await cursor.close()
    await db.commit()
    
    return row[0] if row else None


async def get_user_by_telegram_id(db: aiosqlite.Connection, telegram_id: int) -> Optional[dict]:
    """Get user by Telegram ID."""
    cursor = await db.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    return dict(row) if row else None


async def get_user_by_referral_code(db: aiosqlite.Connection, referral_code: str) -> Optional[dict]:
    """Get user by referral code."""
    cursor = await db.execute(
        "SELECT * FROM users WHERE referral_code = ?",
        (referral_code,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    return dict(row) if row else None


async def update_user_total_spent(db: aiosqlite.Connection, user_id: int, amount: int):
    """Update user's total spent amount."""
    await db.execute(
        """UPDATE users 
           SET total_spent = total_spent + ?,
               is_vip = CASE WHEN total_spent + ? >= 10000 THEN 1 ELSE is_vip END
           WHERE id = ?""",
        (amount, amount, user_id)
    )
    await db.commit()


async def get_user_referral_stats(db: aiosqlite.Connection, user_id: int) -> dict:
    """Get user's referral statistics."""
    cursor = await db.execute(
        """SELECT 
               COUNT(DISTINCT u.id) as referee_count,
               COALESCE(SUM(rb.amount), 0) as total_bonuses
           FROM users u
           LEFT JOIN referral_bonuses rb ON rb.referrer_id = ? AND rb.referee_id = u.id
           WHERE u.referred_by_id = ?""",
        (user_id, user_id)
    )
    row = await cursor.fetchone()
    await cursor.close()
    return dict(row) if row else {"referee_count": 0, "total_bonuses": 0}


async def block_user(db: aiosqlite.Connection, user_id: int):
    """Block user."""
    await db.execute(
        "UPDATE users SET is_blocked = 1 WHERE id = ?",
        (user_id,)
    )
    await db.commit()


async def unblock_user(db: aiosqlite.Connection, user_id: int):
    """Unblock user."""
    await db.execute(
        "UPDATE users SET is_blocked = 0 WHERE id = ?",
        (user_id,)
    )
    await db.commit()


async def get_user_by_id(db: aiosqlite.Connection, user_id: int) -> Optional[dict]:
    """Get user by internal ID."""
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    await cursor.close()
    return dict(row) if row else None


async def grant_vip_status(db: aiosqlite.Connection, user_id: int):
    """Grant VIP status to user."""
    await db.execute(
        "UPDATE users SET is_vip = 1 WHERE id = ?",
        (user_id,)
    )
    await db.commit()
