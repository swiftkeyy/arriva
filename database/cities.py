"""City management database operations."""
import aiosqlite
from typing import List


async def get_all_cities(db: aiosqlite.Connection) -> List[str]:
    """Get all cities from settings."""
    cursor = await db.execute(
        "SELECT value FROM settings WHERE key = 'delivery_cities'"
    )
    row = await cursor.fetchone()
    await cursor.close()
    
    if row:
        cities_str = row[0]
        return [city.strip() for city in cities_str.split(',') if city.strip()]
    return []


async def add_city(db: aiosqlite.Connection, city_name: str) -> bool:
    """Add a new city to delivery cities."""
    cities = await get_all_cities(db)
    
    # Check if city already exists (case-insensitive)
    if any(c.lower() == city_name.lower() for c in cities):
        return False
    
    cities.append(city_name)
    cities_str = ','.join(cities)
    
    cursor = await db.execute(
        "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'delivery_cities'",
        (cities_str,)
    )
    await db.commit()
    await cursor.close()
    return True


async def remove_city(db: aiosqlite.Connection, city_name: str) -> bool:
    """Remove a city from delivery cities."""
    cities = await get_all_cities(db)
    
    # Find and remove city (case-insensitive)
    original_count = len(cities)
    cities = [c for c in cities if c.lower() != city_name.lower()]
    
    if len(cities) == original_count:
        return False  # City not found
    
    cities_str = ','.join(cities)
    
    cursor = await db.execute(
        "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'delivery_cities'",
        (cities_str,)
    )
    await db.commit()
    await cursor.close()
    return True
