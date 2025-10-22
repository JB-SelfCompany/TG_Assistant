"""Database models"""

import aiosqlite
from datetime import datetime
from typing import Optional, List
from pathlib import Path


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Establish database connection"""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row
        await self._create_tables()
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist"""
        async with self.connection.cursor() as cursor:
            # Tasks table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TIMESTAMP NOT NULL,
                    last_reminded_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_completed BOOLEAN DEFAULT 0
                )
            """)
            
            # Birthdays table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS birthdays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    birth_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            """)
            
            # User settings table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    city TEXT,
                    country TEXT,
                    region TEXT,
                    timezone TEXT,
                    language TEXT DEFAULT 'ru',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily messages table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_messages (
                    user_id INTEGER PRIMARY KEY,
                    message_id INTEGER NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await self.connection.commit()


class TaskRepository:
    """Task data access layer"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_task(
        self,
        user_id: int,
        title: str,
        description: str,
        due_date: datetime
    ) -> int:
        """Create new task"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO tasks (user_id, title, description, due_date)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, title, description, due_date.isoformat())
            )
            await self.db.connection.commit()
            return cursor.lastrowid
    
    async def get_user_tasks(
        self,
        user_id: int,
        include_completed: bool = False
    ) -> List[aiosqlite.Row]:
        """Get all tasks for user"""
        query = """
            SELECT * FROM tasks
            WHERE user_id = ?
        """
        if not include_completed:
            query += " AND is_completed = 0"
        query += " ORDER BY due_date ASC"
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, (user_id,))
            return await cursor.fetchall()
    
    async def get_task_by_id(self, task_id: int) -> Optional[aiosqlite.Row]:
        """Get task by ID"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            return await cursor.fetchone()
    
    async def update_task_reminder(
        self,
        task_id: int,
        last_reminded_at: datetime
    ) -> None:
        """Update task last reminded time"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE tasks
                SET last_reminded_at = ?
                WHERE id = ?
                """,
                (last_reminded_at.isoformat(), task_id)
            )
            await self.db.connection.commit()
    
    async def postpone_task(
        self,
        task_id: int,
        new_due_date: datetime
    ) -> None:
        """Postpone task to new due date"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE tasks
                SET due_date = ?, last_reminded_at = NULL
                WHERE id = ?
                """,
                (new_due_date.isoformat(), task_id)
            )
            await self.db.connection.commit()
    
    async def delete_task(self, task_id: int) -> None:
        """Delete task"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await self.db.connection.commit()
    
    async def complete_task(self, task_id: int) -> None:
        """Mark task as completed"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE tasks SET is_completed = 1 WHERE id = ?",
                (task_id,)
            )
            await self.db.connection.commit()
    
    async def get_pending_tasks(self) -> List[aiosqlite.Row]:
        """Get all pending tasks that need reminders"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM tasks
                WHERE is_completed = 0
                AND due_date <= datetime('now')
                ORDER BY due_date ASC
                """
            )
            return await cursor.fetchall()


class BirthdayRepository:
    """Birthday data access layer"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def add_birthday(
        self,
        user_id: int,
        name: str,
        birth_date: datetime
    ) -> int:
        """Add new birthday"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO birthdays (user_id, name, birth_date)
                VALUES (?, ?, ?)
                """,
                (user_id, name, birth_date.date().isoformat())
            )
            await self.db.connection.commit()
            return cursor.lastrowid
    
    async def get_user_birthdays(self, user_id: int) -> List[aiosqlite.Row]:
        """Get all birthdays for user"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM birthdays
                WHERE user_id = ?
                ORDER BY birth_date ASC
                """,
                (user_id,)
            )
            return await cursor.fetchall()
    
    async def delete_birthday(self, user_id: int, name: str) -> None:
        """Delete birthday"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM birthdays WHERE user_id = ? AND name = ?",
                (user_id, name)
            )
            await self.db.connection.commit()
    
    async def get_all_birthdays(self) -> List[aiosqlite.Row]:
        """Get all birthdays for reminder checking"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM birthdays")
            return await cursor.fetchall()


class UserSettingsRepository:
    """User settings data access layer"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_settings(self, user_id: int) -> Optional[aiosqlite.Row]:
        """Get user settings"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchone()
    
    async def update_settings(
        self,
        user_id: int,
        city: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> None:
        """Update user settings"""
        async with self.db.connection.cursor() as cursor:
            # Check if settings exist
            await cursor.execute(
                "SELECT user_id FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            exists = await cursor.fetchone()
            
            if exists:
                # Update existing settings
                updates = []
                values = []
                
                if city is not None:
                    updates.append("city = ?")
                    values.append(city)
                if country is not None:
                    updates.append("country = ?")
                    values.append(country)
                if region is not None:
                    updates.append("region = ?")
                    values.append(region)
                if timezone is not None:
                    updates.append("timezone = ?")
                    values.append(timezone)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_id)
                
                query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
                await cursor.execute(query, values)
            else:
                # Insert new settings
                await cursor.execute(
                    """
                    INSERT INTO user_settings (user_id, city, country, region, timezone)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, city, country, region, timezone)
                )
            
            await self.db.connection.commit()


class DailyMessageRepository:
    """Daily message tracking repository (NEW)"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def save_message(self, user_id: int, message_id: int) -> None:
        """Save or update daily message ID"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO daily_messages (user_id, message_id, sent_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (user_id, message_id)
            )
            await self.db.connection.commit()
    
    async def get_message(self, user_id: int) -> Optional[aiosqlite.Row]:
        """Get daily message for user"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM daily_messages WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchone()
    
    async def delete_message(self, user_id: int) -> None:
        """Delete daily message record"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM daily_messages WHERE user_id = ?",
                (user_id,)
            )
            await self.db.connection.commit()
    
    async def get_all_messages(self) -> List[aiosqlite.Row]:
        """Get all daily messages"""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM daily_messages")
            return await cursor.fetchall()