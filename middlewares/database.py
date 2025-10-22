"""Database middleware"""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.models import (
    Database, 
    TaskRepository, 
    BirthdayRepository, 
    UserSettingsRepository,
    DailyMessageRepository
)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database repositories"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.task_repo = TaskRepository(db)
        self.birthday_repo = BirthdayRepository(db)
        self.settings_repo = UserSettingsRepository(db)
        self.daily_message_repo = DailyMessageRepository(db)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Add repositories to handler data"""
        data["task_repo"] = self.task_repo
        data["birthday_repo"] = self.birthday_repo
        data["settings_repo"] = self.settings_repo
        data["daily_message_repo"] = self.daily_message_repo
        return await handler(event, data)