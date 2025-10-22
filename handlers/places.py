"""Places handlers"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from geopy.geocoders import Nominatim

from database.models import UserSettingsRepository
from keyboards.menu import get_places_menu, get_cancel_button
from services.places_service import places_service
from states.user_states import PlacesStates

router = Router(name="places")
logger = logging.getLogger(__name__)

# Geocoder for address to coordinates
geolocator = Nominatim(user_agent="telegram_bot_places")

RESULTS_PER_PAGE = 10


def get_place_type_keyboard(latitude: float, longitude: float) -> InlineKeyboardBuilder:
    """Generate keyboard for place type selection"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💊 Аптеки", callback_data=f"places:search:pharmacies:{latitude}:{longitude}")
    builder.button(text="🏥 Ветаптеки", callback_data=f"places:search:vet:{latitude}:{longitude}")
    builder.button(text="🛒 Продукты", callback_data=f"places:search:shops:{latitude}:{longitude}")
    builder.button(text="📍 Другое место", callback_data="places:location")
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    builder.adjust(3, 2)
    return builder


def get_places_pagination_keyboard(
    place_type: str,
    latitude: float,
    longitude: float,
    page: int,
    total_pages: int
) -> InlineKeyboardBuilder:
    """Generate pagination keyboard for places list"""
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(("⬅️", f"places:page:{place_type}:{latitude}:{longitude}:{page - 1}"))
    
    nav_buttons.append((f"📄 {page + 1}/{total_pages}", "places:page:current"))
    
    if page < total_pages - 1:
        nav_buttons.append(("➡️", f"places:page:{place_type}:{latitude}:{longitude}:{page + 1}"))
    
    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)
    
    # Back buttons
    builder.button(text="🔄 Другой тип", callback_data=f"places:types:{latitude}:{longitude}")
    builder.button(text="◀️ Назад", callback_data=f"places:types:{latitude}:{longitude}")
    
    builder.adjust(len(nav_buttons), 2)
    return builder


@router.callback_query(F.data == "menu:places")
async def show_places_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Show places menu"""
    # Check if we have saved location in state
    data = await state.get_data()
    
    if data.get("latitude") and data.get("longitude"):
        # Show place types if location is already set
        latitude = data["latitude"]
        longitude = data["longitude"]
        
        try:
            await callback.message.edit_text(
                text="📍 <b>Выберите тип места</b>\n\nЧто вы хотите найти?",
                reply_markup=get_place_type_keyboard(latitude, longitude).as_markup()
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
    else:
        # Ask for location
        try:
            await callback.message.edit_text(
                text=(
                    "📍 <b>Места рядом</b>\n\n"
                    "Найдите ближайшие аптеки, ветаптеки и продуктовые магазины.\n\n"
                    "Для начала укажите местоположение:"
                ),
                reply_markup=get_places_menu()
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
    
    await callback.answer()


@router.callback_query(F.data == "places:location")
async def request_location(callback: CallbackQuery, state: FSMContext) -> None:
    """Request user location"""
    await state.set_state(PlacesStates.waiting_for_location)
    
    # Save message ID to edit it later
    await state.update_data(message_id=callback.message.message_id)
    
    try:
        await callback.message.edit_text(
            text=(
                "📍 <b>Укажите местоположение</b>\n\n"
                "Отправьте:\n"
                "• Геолокацию (через кнопку 📎 → Местоположение)\n"
                "• Или адрес текстом (например: <code>Пушкина 36</code>)"
            ),
            reply_markup=get_cancel_button()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.message(PlacesStates.waiting_for_location, F.location)
async def process_location_coords(
    message: Message,
    state: FSMContext
) -> None:
    """Process location from geolocation"""
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    
    # Delete user's message
    await message.delete()
    
    data = await state.get_data()
    
    # Save location to state
    await state.update_data(latitude=latitude, longitude=longitude)
    await state.clear()
    
    text = (
        "📍 <b>Местоположение получено</b>\n\n"
        "Что вы хотите найти рядом?"
    )
    
    # Edit the original message
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data.get("message_id"),
            text=text,
            reply_markup=get_place_type_keyboard(latitude, longitude).as_markup()
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")


@router.message(PlacesStates.waiting_for_location, F.text)
async def process_location_address(
    message: Message,
    state: FSMContext,
    settings_repo: UserSettingsRepository
) -> None:
    """Process location from text address"""
    address = message.text.strip()
    
    # Delete user's message
    try:
        await message.delete()
    except:
        pass
    
    data = await state.get_data()
    message_id = data.get("message_id")
    
    if not message_id:
        logger.error("No message_id in state")
        return
    
    # Get user's city as base
    user_settings = await settings_repo.get_settings(message.from_user.id)
    base_city = user_settings["city"] if user_settings and user_settings["city"] else "Moscow"
    
    # Geocode address
    full_address = f"{address}, {base_city}, Russia"
    
    try:
        location = geolocator.geocode(full_address, timeout=10)
        
        if not location:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    text=(
                        "📍 <b>Укажите местоположение</b>\n\n"
                        "❌ Не удалось найти указанный адрес.\n"
                        "Попробуйте указать более точный адрес.\n\n"
                        "Отправьте:\n"
                        "• Геолокацию (через кнопку 📎 → Местоположение)\n"
                        "• Или адрес текстом (например: <code>Пушкина 36</code>)"
                    ),
                    reply_markup=get_cancel_button()
                )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
            return
        
        latitude = location.latitude
        longitude = location.longitude
        
        # Save location to state
        await state.update_data(latitude=latitude, longitude=longitude)
        await state.clear()
        
        text = (
            f"📍 <b>Найдено:</b> {location.address}\n\n"
            "Что вы хотите найти рядом?"
        )
        
        # Edit the original message
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message_id,
                text=text,
                reply_markup=get_place_type_keyboard(latitude, longitude).as_markup()
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
        
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message_id,
                text=(
                    "📍 <b>Укажите местоположение</b>\n\n"
                    "❌ Ошибка при поиске адреса.\n"
                    "Попробуйте еще раз.\n\n"
                    "Отправьте:\n"
                    "• Геолокацию (через кнопку 📎 → Местоположение)\n"
                    "• Или адрес текстом (например: <code>Пушкина 36</code>)"
                ),
                reply_markup=get_cancel_button()
            )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")


@router.callback_query(F.data.startswith("places:search:"))
async def search_places(callback: CallbackQuery, state: FSMContext) -> None:
    """Search for places"""
    parts = callback.data.split(":")
    place_type = parts[2]
    latitude = float(parts[3])
    longitude = float(parts[4])
    
    # Save location to state if not already saved
    await state.update_data(latitude=latitude, longitude=longitude)
    
    await callback.answer("🔍 Поиск мест...")
    
    # Search places
    results = await places_service.search_places(latitude, longitude, place_type)
    
    if not results:
        try:
            await callback.message.edit_text(
                text="❌ По вашему запросу ничего не найдено в радиусе 2 км.",
                reply_markup=get_place_type_keyboard(latitude, longitude).as_markup()
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        return
    
    # Show first page
    await show_places_page(callback, place_type, latitude, longitude, results, page=0)


@router.callback_query(F.data.startswith("places:page:"))
async def places_pagination(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle places pagination"""
    parts = callback.data.split(":")
    page_str = parts[-1]
    
    if page_str == "current":
        await callback.answer()
        return
    
    place_type = parts[2]
    latitude = float(parts[3])
    longitude = float(parts[4])
    page = int(parts[5])
    
    # Save location to state
    await state.update_data(latitude=latitude, longitude=longitude)
    
    # Re-search places
    results = await places_service.search_places(latitude, longitude, place_type)
    
    await show_places_page(callback, place_type, latitude, longitude, results, page)


@router.callback_query(F.data.startswith("places:types:"))
async def show_place_types(callback: CallbackQuery, state: FSMContext) -> None:
    """Show place type selection again"""
    parts = callback.data.split(":")
    latitude = float(parts[2])
    longitude = float(parts[3])
    
    # Save location to state
    await state.update_data(latitude=latitude, longitude=longitude)
    
    try:
        await callback.message.edit_text(
            text="📍 <b>Выберите тип места</b>\n\nЧто вы хотите найти?",
            reply_markup=get_place_type_keyboard(latitude, longitude).as_markup()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


async def show_places_page(
    callback: CallbackQuery,
    place_type: str,
    latitude: float,
    longitude: float,
    results: list,
    page: int = 0
) -> None:
    """Show places page with pagination"""
    total_places = len(results)
    total_pages = (total_places + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    
    # Ensure page is within bounds
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * RESULTS_PER_PAGE
    end_idx = min(start_idx + RESULTS_PER_PAGE, total_places)
    
    page_results = results[start_idx:end_idx]
    
    # Get place type info
    config = places_service.PLACE_TYPES[place_type]
    
    # Build text
    text = f"{config['emoji']} <b>{config['name']}</b> (стр. {page + 1}/{total_pages})\n"
    text += f"<i>Найдено: {total_places}</i>\n\n"
    
    for i, place in enumerate(page_results, start=start_idx + 1):
        text += places_service.format_place(place, i) + "\n\n"
    
    # Generate keyboard
    keyboard = get_places_pagination_keyboard(
        place_type, latitude, longitude, page, total_pages
    )
    
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard.as_markup()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()