import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.models import Database
from middlewares.database import DatabaseMiddleware
from utils.logger import setup_logging
from utils.scheduler import BotScheduler

# Import routers
from handlers import start, tasks, birthdays, weather, currency, places, settings as settings_handler

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main function"""
    # Setup logging
    setup_logging()
    
    logger.info("=" * 50)
    logger.info("Starting Telegram Bot")
    logger.info("=" * 50)
    
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher with FSM storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Initialize database and connect BEFORE creating middleware
    db = Database(settings.database_path)
    await db.connect()
    logger.info("Database connected")
    
    # Setup middleware AFTER database connection
    db_middleware = DatabaseMiddleware(db)
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)
    
    # Initialize scheduler (UPDATED with daily_message_repo)
    scheduler = BotScheduler(
        bot=bot,
        task_repo=db_middleware.task_repo,
        birthday_repo=db_middleware.birthday_repo,
        daily_message_repo=db_middleware.daily_message_repo  # NEW
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(birthdays.router)
    dp.include_router(weather.router)
    dp.include_router(currency.router)
    dp.include_router(places.router)
    dp.include_router(settings_handler.router)
    
    try:
        # Start polling
        logger.info("Starting polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Bot shutting down...")
        
        # Stop scheduler
        scheduler.stop()
        logger.info("Scheduler stopped")
        
        # Close database connection
        await db.disconnect()
        logger.info("Database disconnected")
        
        # Close bot session
        await bot.session.close()
        logger.info("Bot session closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)