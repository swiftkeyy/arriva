"""Referral database operations for SQLite."""
import aiosqlite
from typing import Optional
import config


async def create_referral_bonus(
    db: aiosqlite.Connection,
    referrer_id: int,
    referee_id: int,
    order_id: int,
    amount: int
):
    """Create referral bonus record."""
    await db.execute(
        """INSERT INTO referral_bonuses (referrer_id, referee_id, order_id, amount)
           VALUES (?, ?, ?, ?)""",
        (referrer_id, referee_id, order_id, amount)
    )
    await db.commit()


async def get_referral_stats(db: aiosqlite.Connection, user_id: int) -> dict:
    """Get referral statistics for user."""
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
    return dict(row) if row else {"referee_count": 0, "total_bonuses": 0}


async def get_all_referral_stats(db: aiosqlite.Connection) -> list[dict]:
    """Get all referral statistics."""
    cursor = await db.execute(
        """SELECT 
               u.id, u.username, u.telegram_id,
               COUNT(DISTINCT ref.id) as referee_count,
               COALESCE(SUM(rb.amount), 0) as total_bonuses
           FROM users u
           LEFT JOIN users ref ON ref.referred_by_id = u.id
           LEFT JOIN referral_bonuses rb ON rb.referrer_id = u.id
           GROUP BY u.id, u.username, u.telegram_id
           HAVING COUNT(DISTINCT ref.id) > 0
           ORDER BY total_bonuses DESC"""
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def process_referral_bonus(db: aiosqlite.Connection, referee_id: int, order_id: int):
    """Process referral bonus if this is referee's first completed order."""
    # Check if this is first completed order
    cursor = await db.execute(
        """SELECT COUNT(*) FROM orders 
           WHERE user_id = ? AND status = 'completed'""",
        (referee_id,)
    )
    row = await cursor.fetchone()
    completed_orders = row[0] if row else 0
    
    if completed_orders != 1:
        return  # Not first order
    
    # Get referrer
    cursor = await db.execute(
        "SELECT referred_by_id FROM users WHERE id = ?",
        (referee_id,)
    )
    row = await cursor.fetchone()
    
    if not row or not row[0]:
        return  # No referrer
    
    referrer_id = row[0]
    
    # Create bonus
    await create_referral_bonus(
        db, referrer_id, referee_id, order_id, config.REFERRAL_BONUS_AMOUNT
    )
