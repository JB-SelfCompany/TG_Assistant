"""Birthday management handlers"""

import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from database.models import BirthdayRepository
from keyboards.menu import get_birthdays_menu, get_cancel_button
from states.user_states import BirthdayStates

router = Router(name="birthdays")
logger = logging.getLogger(__name__)

# Pagination settings
BIRTHDAYS_PER_PAGE = 10


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@router.callback_query(F.data == "menu:birthdays")
async def show_birthdays_menu(
    callback: CallbackQuery,
    birthday_repo: BirthdayRepository
) -> None:
    """Show birthdays list when menu button is clicked"""
    await show_birthdays_page(callback, birthday_repo, page=0)


@router.callback_query(F.data == "bd:add")
async def add_birthday_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start birthday creation process"""
    await state.set_state(BirthdayStates.waiting_for_name)
    await state.update_data(message_id=callback.message.message_id)
    
    await callback.message.edit_text(
        text=(
            "<b>➕ Новый день рождения</b>\n\n"
            "Введите имя человека:"
        ),
        reply_markup=get_cancel_button()
    )
    await callback.answer()


@router.message(BirthdayStates.waiting_for_name)
async def process_birthday_name(message: Message, state: FSMContext) -> None:
    """Process birthday name"""
    name = message.text.strip()
    await message.delete()
    
    if len(name) < 2:
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новый день рождения</b>\n\n"
                    "❌ Имя слишком короткое. Минимум 2 символа.\n\n"
                    "Введите имя человека:"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    if len(name) > 100:
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новый день рождения</b>\n\n"
                    "❌ Имя слишком длинное. Максимум 100 символов.\n\n"
                    "Введите имя человека:"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    await state.update_data(name=name)
    await state.set_state(BirthdayStates.waiting_for_date)
    
    data = await state.get_data()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["message_id"],
        text=(
            "<b>➕ Новый день рождения</b>\n\n"
            "Введите дату рождения в формате:\n"
            "<code>ДД.ММ.ГГГГ</code>\n\n"
            "Например: <code>15.03.1990</code>"
        ),
        reply_markup=get_cancel_button()
    )


@router.message(BirthdayStates.waiting_for_date)
async def process_birthday_date(
    message: Message,
    state: FSMContext,
    birthday_repo: BirthdayRepository
) -> None:
    """Process birthday date"""
    date_str = message.text.strip()
    await message.delete()
    
    data = await state.get_data()
    
    try:
        birth_date = datetime.strptime(date_str, "%d.%m.%Y")
        
        now = datetime.now()
        if birth_date > now:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новый день рождения</b>\n\n"
                    "❌ Дата не может быть в будущем.\n\n"
                    "Введите дату рождения в формате:\n"
                    "<code>ДД.ММ.ГГГГ</code>\n"
                    "Например: <code>15.03.1990</code>"
                ),
                reply_markup=get_cancel_button()
            )
            return
        
        if birth_date.year < 1900:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новый день рождения</b>\n\n"
                    "❌ Слишком старая дата.\n\n"
                    "Введите дату рождения в формате:\n"
                    "<code>ДД.ММ.ГГГГ</code>\n"
                    "Например: <code>15.03.1990</code>"
                ),
                reply_markup=get_cancel_button()
            )
            return
        
        name = data["name"]
        
        await birthday_repo.add_birthday(
            user_id=message.from_user.id,
            name=name,
            birth_date=birth_date
        )
        
        await state.clear()
        
        # Calculate age and days until birthday
        age = now.year - birth_date.year
        next_birthday = birth_date.replace(year=now.year)
        if next_birthday < now:
            next_birthday = birth_date.replace(year=now.year + 1)
        days_until = (next_birthday.date() - now.date()).days
        
        safe_name = escape_html(name)
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["message_id"],
            text=(
                "<b>✅ День рождения добавлен!</b>\n\n"
                f"<b>Имя:</b> {safe_name}\n"
                f"<b>Дата рождения:</b> {birth_date.strftime('%d.%m.%Y')}\n"
                f"<b>Возраст:</b> {age} лет\n"
                f"<b>До дня рождения:</b> {days_until} дней"
            ),
            reply_markup=get_birthdays_menu()
        )
        logger.info(f"Birthday added for user {message.from_user.id}: {name}")
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["message_id"],
            text=(
                "<b>➕ Новый день рождения</b>\n\n"
                "❌ Неверный формат даты.\n\n"
                "Используйте формат:\n"
                "<code>ДД.ММ.ГГГГ</code>\n"
                "Например: <code>15.03.1990</code>"
            ),
            reply_markup=get_cancel_button()
        )


@router.callback_query(F.data.startswith("bd:page:"))
async def birthdays_pagination(
    callback: CallbackQuery,
    birthday_repo: BirthdayRepository
) -> None:
    """Handle birthday list pagination"""
    page_str = callback.data.split(":")[-1]
    
    if page_str == "current":
        await callback.answer()
        return
    
    page = int(page_str)
    await show_birthdays_page(callback, birthday_repo, page)


async def show_birthdays_page(
    callback: CallbackQuery,
    birthday_repo: BirthdayRepository,
    page: int = 0
) -> None:
    """Show birthdays page with pagination - SIMPLE ONE-LINE FORMAT"""
    logger.info(f"show_birthdays_page called for user {callback.from_user.id}, page {page}")
    
    birthdays = await birthday_repo.get_user_birthdays(callback.from_user.id)
    
    if not birthdays:
        logger.info(f"User {callback.from_user.id} has no birthdays")
        try:
            await callback.message.edit_text(
                text="🎂 <b>У вас пока нет сохраненных дней рождения</b>\n\nДобавьте первый день рождения!",
                reply_markup=get_birthdays_menu()
            )
        except TelegramBadRequest as e:
            logger.warning(f"TelegramBadRequest when editing birthdays: {e}")
        await callback.answer()
        return
    
    now = datetime.now()
    
    # Sort by upcoming birthday
    sorted_birthdays = []
    for bd in birthdays:
        try:
            birth_date = datetime.strptime(bd["birth_date"], "%Y-%m-%d")
            next_birthday = birth_date.replace(year=now.year)
            if next_birthday.date() < now.date():
                next_birthday = birth_date.replace(year=now.year + 1)
            days_until = (next_birthday.date() - now.date()).days
            age = now.year - birth_date.year
            
            sorted_birthdays.append({
                "id": bd["id"],
                "name": bd["name"],
                "birth_date": birth_date,
                "days_until": days_until,
                "age": age
            })
        except Exception as bd_error:
            logger.error(f"Error processing birthday {bd.get('id')}: {bd_error}")
            continue
    
    sorted_birthdays.sort(key=lambda x: x["days_until"])
    logger.info(f"Processed {len(sorted_birthdays)} birthdays for user {callback.from_user.id}")
    
    # Pagination
    total_birthdays = len(sorted_birthdays)
    total_pages = (total_birthdays + BIRTHDAYS_PER_PAGE - 1) // BIRTHDAYS_PER_PAGE
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * BIRTHDAYS_PER_PAGE
    end_idx = min(start_idx + BIRTHDAYS_PER_PAGE, total_birthdays)
    page_birthdays = sorted_birthdays[start_idx:end_idx]
    
    logger.info(f"Displaying page {page+1}/{total_pages} ({len(page_birthdays)} birthdays)")
    
    # Build text - ONE-LINE FORMAT with emoji indicators
    text = f"🎂 <b>Дни рождения</b> (стр. {page + 1}/{total_pages})\n\n"
    
    for bd in page_birthdays:
        safe_name = escape_html(bd["name"][:30])
        birth_date_str = bd["birth_date"].strftime("%d.%m")
        days_until = bd["days_until"]
        
        # Status emoji based on days until birthday
        if days_until == 0:
            status = "🔴"
            days_text = "<b>СЕГОДНЯ! 🎉</b>"
        elif days_until <= 3:
            status = "🔴"  # Very soon (0-3 days)
            days_text = f"через {days_until} дн."
        elif days_until <= 7:
            status = "🟡"  # Soon (4-7 days)
            days_text = f"через {days_until} дн."
        elif days_until <= 30:
            status = "🟢"  # This month (8-30 days)
            days_text = f"через {days_until} дн."
        else:
            status = "⚪"  # Far future (>30 days)
            days_text = f"через {days_until} дн."
        
        # One-line format: emoji name (age лет) • date • days
        text += f"{status} <b>{safe_name}</b> ({bd['age']} лет) • {birth_date_str} • {days_text}\n"
    
    # Build keyboard
    builder = InlineKeyboardBuilder()
    
    # Pagination buttons
    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Пред.", callback_data=f"bd:page:{page - 1}")
        else:
            builder.button(text="⬅️ •", callback_data="bd:page:current")
            
        builder.button(text=f"{page + 1}/{total_pages}", callback_data="bd:page:current")
        
        if page < total_pages - 1:
            builder.button(text="След. ➡️", callback_data=f"bd:page:{page + 1}")
        else:
            builder.button(text="• ➡️", callback_data="bd:page:current")
        
        builder.adjust(3)
    
    # Action buttons
    builder.button(text="➕ Добавить", callback_data="bd:add")
    builder.button(text="🗑 Удалить", callback_data="bd:delete")
    
    # Back button
    builder.button(text="◀️ Назад", callback_data="menu:main")
    
    # Adjust layout
    if total_pages > 1:
        builder.adjust(3, 2, 1)  # pagination (3), actions (2), back (1)
    else:
        builder.adjust(2, 1)  # actions (2), back (1)
    
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        logger.info(f"Successfully updated birthdays for user {callback.from_user.id}")
    except TelegramBadRequest as e:
        logger.warning(f"TelegramBadRequest when updating birthdays: {e}")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error updating birthdays message: {e}", exc_info=True)
        await callback.answer("❌ Ошибка обновления", show_alert=True)

@router.callback_query(F.data == "bd:delete")
async def delete_birthday_start(
    callback: CallbackQuery,
    birthday_repo: BirthdayRepository
) -> None:
    """Start birthday deletion"""
    birthdays = await birthday_repo.get_user_birthdays(callback.from_user.id)
    
    if not birthdays:
        await callback.answer("У вас нет сохраненных дней рождения", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    
    for bd in birthdays:
        birth_date = datetime.strptime(bd["birth_date"], "%Y-%m-%d")
        name = bd["name"]
        builder.button(
            text=f"{name} • {birth_date.strftime('%d.%m.%Y')}",
            callback_data=f"bd:delete_confirm:{name}"
        )
    
    builder.button(text="◀️ Назад", callback_data="menu:birthdays")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text="<b>🗑 Удаление дня рождения</b>\n\nВыберите, чей день рождения удалить:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("bd:delete_confirm:"))
async def delete_birthday_confirm(
    callback: CallbackQuery,
    birthday_repo: BirthdayRepository
) -> None:
    """Confirm birthday deletion"""
    name = ":".join(callback.data.split(":")[2:])
    
    await birthday_repo.delete_birthday(callback.from_user.id, name)
    
    safe_name = escape_html(name)
    
    await callback.message.edit_text(
        text=f"✅ День рождения <b>{safe_name}</b> удален",
        reply_markup=get_birthdays_menu()
    )
    await callback.answer("✅ Удалено!")
    logger.info(f"Birthday deleted for user {callback.from_user.id}: {name}")