"""Keyboard layouts"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """
    Главное меню бота - оптимизированная версия
    """
    builder = InlineKeyboardBuilder()
    
    # Main menu buttons
    buttons = [
        ("📋 Задачи", "menu:tasks"),
        ("🎂 Дни рождения", "menu:birthdays"),
        ("🌤 Погода", "menu:weather"),
        ("💱 Валюты", "menu:currency"),
        ("📍 Места рядом", "menu:places"),
        ("⚙️ Настройки", "menu:settings"),
    ]
    
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    
    builder.adjust(2)  # 2 buttons per row
    return builder.as_markup()


def get_tasks_menu() -> InlineKeyboardMarkup:
    """Tasks submenu - без кнопки 'Список задач'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ Добавить задачу", callback_data="task:add")
    builder.button(text="🗑 Удалить задачу", callback_data="task:delete")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_birthdays_menu() -> InlineKeyboardMarkup:
    """Birthdays submenu - без кнопки 'Список дней рождения'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="➕ Добавить день рождения", callback_data="bd:add")
    builder.button(text="🗑 Удалить день рождения", callback_data="bd:delete")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(2, 1)
    return builder.as_markup()


def get_weather_menu() -> InlineKeyboardMarkup:
    """Weather submenu - без кнопки 'Текущая погода'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Прогноз на 5 дней", callback_data="weather:forecast")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(1, 1)
    return builder.as_markup()


def get_currency_menu() -> InlineKeyboardMarkup:
    """Currency submenu - без кнопки 'Курсы валют'"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Конвертация", callback_data="currency:convert")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(1, 1)
    return builder.as_markup()


def get_places_menu() -> InlineKeyboardMarkup:
    """Places submenu"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💊 Аптеки", callback_data="places:pharmacies")
    builder.button(text="🏥 Ветаптеки", callback_data="places:vet")
    builder.button(text="🛒 Продукты", callback_data="places:shops")
    builder.button(text="📍 Настроить местоположение", callback_data="places:location")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(3, 2)
    return builder.as_markup()


def get_cancel_button() -> InlineKeyboardMarkup:
    """Cancel button for FSM states"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()


def get_back_button(callback_data: str) -> InlineKeyboardMarkup:
    """Back button"""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=callback_data)
    return builder.as_markup()


def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Confirmation keyboard for delete actions"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Да", callback_data=f"{action}:confirm:{item_id}")
    builder.button(text="❌ Нет", callback_data=f"{action}:cancel")
    
    builder.adjust(2)
    return builder.as_markup()


def get_postpone_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Postpone task keyboard"""
    builder = InlineKeyboardBuilder()
    
    postpone_options = [
        ("5 минут", 5),
        ("10 минут", 10),
        ("30 минут", 30),
        ("1 час", 60),
        ("3 часа", 180),
        ("1 день", 1440),
    ]
    
    for text, minutes in postpone_options:
        builder.button(
            text=text,
            callback_data=f"task:postpone:{task_id}:{minutes}"
        )
    
    builder.button(text="◀️ Назад", callback_data=f"task:actions:{task_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_task_action_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Task action buttons"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Выполнено", callback_data=f"task:complete:{task_id}")
    builder.button(text="⏰ Отложить", callback_data=f"task:postpone_menu:{task_id}")
    builder.button(text="🗑 Удалить", callback_data=f"task:delete_confirm:{task_id}")
    builder.button(text="◀️ К списку", callback_data="menu:tasks")
    
    builder.adjust(2, 1, 1)
    return builder.as_markup()