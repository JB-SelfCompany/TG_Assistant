"""Weather handlers"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import UserSettingsRepository
from keyboards.menu import get_weather_menu
from services.weather_service import WeatherService

router = Router(name="weather")
logger = logging.getLogger(__name__)

weather_service = WeatherService()


@router.callback_query(F.data == "menu:weather")
async def show_weather_menu(
    callback: CallbackQuery,
    state: FSMContext,
    settings_repo: UserSettingsRepository
) -> None:
    """Show current weather immediately (UPDATED)"""
    await state.clear()
    
    # Immediately show current weather instead of menu
    await show_current_weather(callback, settings_repo)


async def show_current_weather(
    callback: CallbackQuery,
    settings_repo: UserSettingsRepository
) -> None:
    """Show current weather"""
    # Get user's city
    user_settings = await settings_repo.get_settings(callback.from_user.id)
    city = user_settings["city"] if user_settings and user_settings["city"] else "Moscow"
    
    # Get weather data
    weather_data = await weather_service.get_current_weather(city)
    
    if not weather_data:
        await callback.message.edit_text(
            text="❌ Не удалось получить данные о погоде.\nПопробуйте позже.",
            reply_markup=get_weather_menu()
        )
        await callback.answer()
        return
    
    text = weather_service.format_current_weather(weather_data)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_weather_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "weather:forecast")
async def show_weather_forecast(
    callback: CallbackQuery,
    settings_repo: UserSettingsRepository
) -> None:
    """Show 5-day weather forecast"""
    # Get user's city
    user_settings = await settings_repo.get_settings(callback.from_user.id)
    city = user_settings["city"] if user_settings and user_settings["city"] else "Moscow"
    
    # Get forecast data
    forecast_data = await weather_service.get_forecast(city)
    
    if not forecast_data:
        await callback.message.edit_text(
            text="❌ Не удалось получить прогноз погоды.\nПопробуйте позже.",
            reply_markup=get_weather_menu()
        )
        await callback.answer()
        return
    
    text = weather_service.format_forecast(forecast_data)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_weather_menu()
    )
    await callback.answer()