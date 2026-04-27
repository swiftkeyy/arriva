"""Meeting database operations for SQLite."""
import aiosqlite
from typing import List, Optional


async def create_meeting(db: aiosqlite.Connection, order_id: int, user_id: int) -> int:
    """Create meeting record."""
    cursor = await db.execute(
        """INSERT INTO meetings (order_id, user_id, status)
           VALUES (?, ?, 'pending')""",
        (order_id, user_id)
    )
    await db.commit()
    return cursor.lastrowid


async def get_meetings_by_status(db: aiosqlite.Connection, status: str) -> List[dict]:
    """Get meetings by status."""
    cursor = await db.execute(
        """SELECT m.*, o.order_number, u.username, u.telegram_id
           FROM meetings m
           JOIN orders o ON m.order_id = o.id
           JOIN users u ON m.user_id = u.id
           WHERE m.status = ?
           ORDER BY m.created_at DESC""",
        (status,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def cancel_meeting_by_order(db: aiosqlite.Connection, order_id: int) -> bool:
    """Cancel meeting by order_id. Returns True if cancelled."""
    cursor = await db.execute(
        "UPDATE meetings SET status = 'cancelled' WHERE order_id = ? AND status = 'pending'",
        (order_id,)
    )
    await db.commit()
    return cursor.rowcount > 0

    db: aiosqlite.Connection,
    meeting_id: int,
    status: str,
    scheduled_time: Optional[str] = None,
    location: Optional[str] = None
):
    """Update meeting status."""
    if scheduled_time and location:
        await db.execute(
            """UPDATE meetings 
               SET status = ?, scheduled_time = ?, location = ?
               WHERE id = ?""",
            (status, scheduled_time, location, meeting_id)
        )
    else:
        await db.execute(
            "UPDATE meetings SET status = ? WHERE id = ?",
            (status, meeting_id)
        )
    
    await db.commit()
