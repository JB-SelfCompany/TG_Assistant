"""Background task scheduler"""

import logging
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Callable, Dict
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.models import TaskRepository, BirthdayRepository, DailyMessageRepository
from config import settings

logger = logging.getLogger(__name__)


class BotScheduler:
    """Scheduler for background tasks"""
    
    def __init__(
        self,
        bot: Bot,
        task_repo: TaskRepository,
        birthday_repo: BirthdayRepository,
        daily_message_repo: DailyMessageRepository
    ):
        self.bot = bot
        self.task_repo = task_repo
        self.birthday_repo = birthday_repo
        self.daily_message_repo = daily_message_repo
        self.scheduler = AsyncIOScheduler(
            timezone=settings.default_timezone
        )
    
    def start(self) -> None:
        """Start scheduler"""
        # Check tasks every 5 minutes
        self.scheduler.add_job(
            self.check_tasks,
            "interval",
            minutes=5,
            id="check_tasks"
        )
        
        # Check birthdays daily at 9:00
        self.scheduler.add_job(
            self.check_birthdays,
            CronTrigger(hour=9, minute=0),
            id="check_birthdays"
        )
        
        # Morning message at 8:00
        self.scheduler.add_job(
            self.send_morning_message,
            CronTrigger(hour=8, minute=0),
            id="morning_message"
        )
        
        # Delete previous message at 23:59
        self.scheduler.add_job(
            self.delete_daily_message,
            CronTrigger(hour=23, minute=59),
            id="delete_daily_message"
        )
        
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    async def check_tasks(self) -> None:
        """Check and send task reminders"""
        try:
            tz = ZoneInfo(settings.default_timezone)
            now = datetime.now(tz)
            pending_tasks = await self.task_repo.get_pending_tasks()
            
            for task in pending_tasks:
                due_date = datetime.fromisoformat(task["due_date"]).replace(tzinfo=tz)
                
                # Check if task is due
                if due_date <= now:
                    # Check if already reminded recently (within 1 hour)
                    if task["last_reminded_at"]:
                        last_reminded = datetime.fromisoformat(
                            task["last_reminded_at"]
                        ).replace(tzinfo=tz)
                        if now - last_reminded < timedelta(hours=1):
                            continue
                    
                    # Send reminder
                    from keyboards.menu import get_task_action_keyboard
                    
                    text = (
                        "⏰ Напоминание о задаче!\n\n"
                        f"📝 {task['title']}\n"
                    )
                    
                    if task["description"]:
                        text += f"📄 {task['description']}\n"
                    
                    text += f"\n📅 Должна была быть выполнена: {due_date.strftime('%d.%m.%Y %H:%M')}"
                    
                    try:
                        await self.bot.send_message(
                            chat_id=task["user_id"],
                            text=text,
                            reply_markup=get_task_action_keyboard(task["id"])
                        )
                        
                        # Update last reminded time
                        await self.task_repo.update_task_reminder(task["id"], now)
                        logger.info(f"Task reminder sent: {task['id']}")
                    except Exception as e:
                        logger.error(f"Error sending task reminder: {e}")
        
        except Exception as e:
            logger.error(f"Error checking tasks: {e}")
    
    async def check_birthdays(self) -> None:
        """Check and send birthday reminders"""
        try:
            now = datetime.now()
            today = now.date()
            all_birthdays = await self.birthday_repo.get_all_birthdays()
            
            for bd in all_birthdays:
                birth_date = datetime.strptime(bd["birth_date"], "%Y-%m-%d").date()
                
                # Check if birthday is today
                if birth_date.day == today.day and birth_date.month == today.month:
                    age = today.year - birth_date.year
                    text = (
                        "🎉 День рождения сегодня!\n\n"
                        f"👤 {bd['name']}\n"
                        f"🎂 Исполняется {age} лет\n\n"
                        "Не забудьте поздравить! 🎁"
                    )
                    
                    try:
                        await self.bot.send_message(
                            chat_id=bd["user_id"],
                            text=text
                        )
                        logger.info(f"Birthday reminder sent for {bd['name']}")
                    except Exception as e:
                        logger.error(f"Error sending birthday reminder: {e}")
                
                # Check if birthday is tomorrow (advance notice)
                tomorrow = today + timedelta(days=1)
                if birth_date.day == tomorrow.day and birth_date.month == tomorrow.month:
                    age = tomorrow.year - birth_date.year
                    text = (
                        "📅 Напоминание!\n\n"
                        f"Завтра день рождения у {bd['name']}\n"
                        f"🎂 Исполняется {age} лет"
                    )
                    
                    try:
                        await self.bot.send_message(
                            chat_id=bd["user_id"],
                            text=text
                        )
                        logger.info(f"Birthday advance notice sent for {bd['name']}")
                    except Exception as e:
                        logger.error(f"Error sending birthday advance notice: {e}")
        
        except Exception as e:
            logger.error(f"Error checking birthdays: {e}")
    
    async def send_morning_message(self) -> None:
        """Send morning message with weather and currency rates (UPDATED)"""
        try:
            from services.weather_service import weather_service
            from services.currency_service import currency_service
            
            now = datetime.now(ZoneInfo(settings.default_timezone))
            formatted_date = now.strftime("%d.%m.%Y")
            
            # Get weather data
            weather_data = await weather_service.get_current_weather(settings.default_city)
            
            # Get currency rates
            currency_rates = await currency_service.get_rates()
            
            # Build message text
            text = f"🌅 Доброе утро!\n\n"
            text += f"🌤 Погода на {formatted_date}:\n\n"
            
            # Add weather
            if weather_data:
                text += weather_service.format_current_weather(weather_data)
            else:
                text += "❌ Не удалось получить данные о погоде.\n"
            
            text += "\n"  # Empty line after weather
            
            # Add currency rates (only major currencies)
            if currency_rates:
                text += self.format_major_currencies(currency_rates, formatted_date)
            else:
                text += "❌ Не удалось получить курсы валют.\n"
            
            try:
                # Send message to admin
                sent_message = await self.bot.send_message(
                    chat_id=settings.admin_user_id,
                    text=text
                )
                
                # Save message ID for later deletion
                await self.daily_message_repo.save_message(
                    user_id=settings.admin_user_id,
                    message_id=sent_message.message_id
                )
                
                logger.info(f"Morning message sent and saved: {sent_message.message_id}")
            except Exception as e:
                logger.error(f"Error sending morning message: {e}")
        
        except Exception as e:
            logger.error(f"Error in send_morning_message: {e}")
    
    async def delete_daily_message(self) -> None:
        """Delete previous daily message at 23:59 (NEW)"""
        try:
            # Get all daily messages
            all_messages = await self.daily_message_repo.get_all_messages()
            
            for msg_record in all_messages:
                user_id = msg_record["user_id"]
                message_id = msg_record["message_id"]
                
                try:
                    # Delete message
                    await self.bot.delete_message(
                        chat_id=user_id,
                        message_id=message_id
                    )
                    
                    # Remove from database
                    await self.daily_message_repo.delete_message(user_id)
                    
                    logger.info(f"Deleted daily message {message_id} for user {user_id}")
                except Exception as e:
                    logger.error(f"Error deleting message {message_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in delete_daily_message: {e}")
    
    def format_major_currencies(self, rates: Dict[str, Dict], formatted_date: str) -> str:
        """Format only major currencies for morning message"""
        text = f"\n💱 Основные курсы валют на {formatted_date}:\n\n"
        
        emoji_map = {
            "USD": "💵",
            "EUR": "💶", 
            "GBP": "💷",
            "JPY": "💴",
            "CHF": "🇨🇭",
            "CNY": "🇨🇳",
            "UAH": "🇺🇦"
        }
        
        priority_currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CNY", "UAH"]
        
        for code in priority_currencies:
            if code in rates:
                rate_data = rates[code]
                emoji = emoji_map.get(code, "💱")
                value = rate_data['value'] / rate_data['nominal']
                text += f"{emoji} {code}: {value:.2f} ₽\n"
        
        return text