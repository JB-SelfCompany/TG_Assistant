"""Settings handlers"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import UserSettingsRepository
from keyboards.menu import get_cancel_button
from states.user_states import SettingsStates
from services.weather_service import WeatherService

router = Router(name="settings")
logger = logging.getLogger(__name__)

weather_service = WeatherService()


def get_settings_menu(city: str) -> InlineKeyboardBuilder:
    """Settings menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📍 Изменить город", callback_data="settings:change_city")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(1)
    return builder


@router.callback_query(F.data == "menu:settings")
async def show_settings_menu(
    callback: CallbackQuery,
    settings_repo: UserSettingsRepository
) -> None:
    """Show settings menu"""
    # Get current user settings
    user_settings = await settings_repo.get_settings(callback.from_user.id)
    
    city = user_settings["city"] if user_settings and user_settings["city"] else "Не задан"
    
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"📍 <b>Текущий город:</b> {city}\n\n"
        "Выберите параметр для изменения:"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_settings_menu(city).as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "settings:change_city")
async def settings_change_city(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Start city change process"""
    await state.set_state(SettingsStates.waiting_for_city)
    
    # Save message ID to edit it later
    await state.update_data(message_id=callback.message.message_id)
    
    await callback.message.edit_text(
        text=(
            "📍 <b>Изменение города</b>\n\n"
            "Введите название города на английском языке:\n\n"
            "Примеры:\n"
            "• <code>Moscow</code>\n"
            "• <code>London</code>\n"
            "• <code>New York</code>"
        ),
        reply_markup=get_cancel_button()
    )
    await callback.answer()


@router.message(SettingsStates.waiting_for_city)
async def process_city_change(
    message: Message,
    state: FSMContext,
    settings_repo: UserSettingsRepository
) -> None:
    """Process city change"""
    city = message.text.strip()
    
    # Delete user's message
    await message.delete()
    
    data = await state.get_data()
    
    # Validate city by trying to get weather
    weather_data = await weather_service.get_current_weather(city)
    
    if not weather_data:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "📍 <b>Изменение города</b>\n\n"
                    "❌ Город не найден. Попробуйте еще раз.\n"
                    "Убедитесь, что название на английском языке.\n\n"
                    "Примеры:\n"
                    "• <code>Moscow</code>\n"
                    "• <code>London</code>\n"
                    "• <code>New York</code>"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    # Save city to user settings
    await settings_repo.update_settings(
        user_id=message.from_user.id,
        city=city
    )
    
    await state.clear()
    
    text = (
        f"✅ <b>Город изменен на {city}</b>\n\n"
        f"🌡 <b>Температура:</b> {weather_data['temperature']}°C\n"
        f"🌤 <b>Погода:</b> {weather_data['description']}\n"
        f"💨 <b>Ветер:</b> {weather_data['wind_speed']} м/с\n"
        f"💧 <b>Влажность:</b> {weather_data['humidity']}%"
    )
    
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["message_id"],
        text=text,
        reply_markup=get_settings_menu(city).as_markup()
    )
    
    logger.info(f"User {message.from_user.id} changed city to {city}")