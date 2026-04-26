"""Main bot entry point."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database.connection import init_db, close_db
from database.db_instance import set_db
from middleware.auth import AuthMiddleware
from middleware.rate_limit import RateLimitMiddleware
from handlers import customer, admin, catalog, cart, checkout, referral, broadcast

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    # Validate configuration
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in environment")
    if not config.ADMIN_IDS:
        logger.warning("No ADMIN_IDS configured")
    
    logger.info("Starting Arriva Vape Bot v4.0")
    logger.info(f"Configured admins: {len(config.ADMIN_IDS)}")
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Initialize database
    try:
        db = await init_db(config.DATABASE_PATH)
        set_db(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Register middleware
    dp.message.middleware(AuthMiddleware(config.ADMIN_IDS))
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(AuthMiddleware(config.ADMIN_IDS))
    
    # Register routers
    dp.include_router(customer.router)
    dp.include_router(admin.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(referral.router)
    dp.include_router(broadcast.router)
    
    logger.info("Bot initialized successfully")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        # Cleanup
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
