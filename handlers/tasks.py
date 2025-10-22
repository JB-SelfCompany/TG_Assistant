"""Task management handlers"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from database.models import TaskRepository
from keyboards.menu import (
    get_tasks_menu,
    get_cancel_button,
    get_task_action_keyboard,
    get_postpone_keyboard,
    get_main_menu
)
from states.user_states import TaskStates
from config import settings

router = Router(name="tasks")
logger = logging.getLogger(__name__)

# Pagination settings
TASKS_PER_PAGE = 10

@router.callback_query(F.data == "menu:tasks")
async def show_tasks_menu(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Show tasks list when menu button is clicked"""
    logger.info(f"User {callback.from_user.id} clicked 'menu:tasks' button")
    
    try:
        await show_tasks_page(callback, task_repo, page=0)
        logger.info(f"Successfully displayed tasks page for user {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error showing tasks menu for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при загрузке задач", show_alert=True)
        try:
            await callback.message.edit_text(
                text="❌ Ошибка загрузки задач\n\nПопробуйте позже",
                reply_markup=get_main_menu()
            )
        except Exception as edit_error:
            logger.error(f"Error editing message: {edit_error}")


async def show_tasks_page(
    callback: CallbackQuery,
    task_repo: TaskRepository,
    page: int = 0
) -> None:
    """Show tasks page with pagination"""
    logger.info(f"show_tasks_page called for user {callback.from_user.id}, page {page}")
    
    try:
        tasks = await task_repo.get_user_tasks(callback.from_user.id)
        logger.info(f"Retrieved {len(tasks) if tasks else 0} tasks for user {callback.from_user.id}")
        
        if not tasks:
            logger.info(f"User {callback.from_user.id} has no tasks")
            try:
                await callback.message.edit_text(
                    text="📋 <b>У вас пока нет активных задач</b>\n\nДобавьте новую задачу, чтобы начать!",
                    reply_markup=get_tasks_menu()
                )
                await callback.answer()
                logger.info(f"Displayed empty tasks message for user {callback.from_user.id}")
            except TelegramBadRequest as e:
                logger.warning(f"TelegramBadRequest when editing message: {e}")
                await callback.answer()
            return
        
        tz = ZoneInfo(settings.default_timezone)
        now = datetime.now(tz)
        
        # Prepare task data
        task_list = []
        for task in tasks:
            try:
                due_date = datetime.fromisoformat(task["due_date"]).replace(tzinfo=tz)
                time_left = due_date - now
                task_list.append({
                    "id": task["id"],
                    "title": task["title"],
                    "description": task["description"] if task["description"] else "",
                    "due_date": due_date,
                    "time_left": time_left
                })
            except Exception as task_error:
                logger.error(f"Error processing task {task.get('id')}: {task_error}")
                continue
        
        logger.info(f"Processed {len(task_list)} tasks successfully")
        
        # Sort by urgency
        task_list.sort(key=lambda x: (x['time_left'].total_seconds() >= 0, abs(x['time_left'].total_seconds())))
        
        # Pagination
        total_tasks = len(task_list)
        total_pages = (total_tasks + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
        page = max(0, min(page, total_pages - 1))
        start_idx = page * TASKS_PER_PAGE
        end_idx = min(start_idx + TASKS_PER_PAGE, total_tasks)
        page_tasks = task_list[start_idx:end_idx]
        
        logger.info(f"Displaying page {page+1}/{total_pages} ({len(page_tasks)} tasks)")
        
        # Build text
        text = f"📋 <b>Ваши задачи</b> (стр. {page + 1}/{total_pages})\n\n"
        
        for i, task in enumerate(page_tasks, start=start_idx + 1):
            time_left = task["time_left"]
            
            # Status emoji
            if time_left.total_seconds() < 0:
                status = "🔴"  # Overdue
            elif time_left.total_seconds() < 3600:
                status = "🟡"  # Soon
            else:
                status = "🟢"  # OK
            
            # Format time left
            if time_left.total_seconds() < 0:
                time_str = "⏰ Просрочено"
            elif time_left.days > 0:
                time_str = f"⏳ {time_left.days} дн."
            elif time_left.seconds >= 3600:
                hours = time_left.seconds // 3600
                time_str = f"⏳ {hours} ч."
            else:
                minutes = time_left.seconds // 60
                time_str = f"⏳ {minutes} мин."
            
            title = escape_html(task["title"][:50])
            date_str = task["due_date"].strftime("%d.%m %H:%M")
            
            text += f"{status} <b>{title}</b>\n"
            text += f"   {date_str} • {time_str}\n\n"
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        
        # Task buttons - each task as separate button
        for task in page_tasks:
            title = task["title"][:30]
            builder.button(
                text=f"📋 {title}",
                callback_data=f"task:actions:{task['id']}"
            )
        
        # Build keyboard
        builder = InlineKeyboardBuilder()
        
        for task in page_tasks:
            title = task["title"][:30]
            builder.button(
                text=f"📋 {title}",
                callback_data=f"task:actions:{task['id']}"
            )
        
        if total_pages > 1:
            if page > 0:
                builder.button(text="⬅️ Пред.", callback_data=f"task:page:{page - 1}")
            else:
                builder.button(text="⬅️ •", callback_data="task:page:current")
                
            builder.button(text=f"📄 {page + 1}/{total_pages}", callback_data="task:page:current")
            
            if page < total_pages - 1:
                builder.button(text="След. ➡️", callback_data=f"task:page:{page + 1}")
            else:
                builder.button(text="• ➡️", callback_data="task:page:current")
        
        builder.button(text="➕ Добавить", callback_data="task:add")
        builder.button(text="🗑 Удалить", callback_data="task:delete")
        
        builder.button(text="◀️ Назад", callback_data="menu:main")
        
        if total_pages > 1:
            builder.adjust(*([1] * len(page_tasks) + [3, 2, 1]))
        else:
            builder.adjust(*([1] * len(page_tasks) + [2, 1]))
        
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            logger.info(f"Successfully updated message with tasks for user {callback.from_user.id}")
        except TelegramBadRequest as e:
            logger.warning(f"TelegramBadRequest when editing tasks message: {e}")
            await callback.answer()
    
    except Exception as e:
        logger.error(f"Critical error in show_tasks_page for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки задач", show_alert=True)
        raise

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_task_compact(task_data: dict, tz: ZoneInfo, now: datetime) -> str:
    """Format task info in compact form"""
    title = escape_html(task_data["title"])
    description = task_data.get("description", "")
    due_date = task_data["due_date"]
    time_left = task_data["time_left"]
    
    date_str = due_date.strftime("%d.%m %H:%M")
    
    # Status emoji and time left text
    if time_left.total_seconds() < 0:
        status = "🔴"
        time_text = "Просрочено!"
    elif time_left.total_seconds() < 3600:
        status = "🟡"
        time_text = f"{int(time_left.total_seconds() / 60)}м"
    elif time_left.days == 0:
        status = "🟡"
        hours = int(time_left.total_seconds() / 3600)
        time_text = f"{hours}ч"
    elif time_left.days <= 3:
        status = "🟢"
        time_text = f"{time_left.days}д"
    else:
        status = "🟢"
        time_text = f"{time_left.days}д"
    
    result = f"{status} <b>{title}</b> • {date_str} • {time_text}"
    
    if description:
        desc_short = escape_html(description[:50])
        if len(description) > 50:
            desc_short += "..."
        result += f"\n   <i>{desc_short}</i>"
    
    result += "\n"
    return result

@router.callback_query(F.data == "task:add")
async def add_task_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Start task creation process"""
    await state.set_state(TaskStates.waiting_for_title)
    await state.update_data(message_id=callback.message.message_id)
    
    await callback.message.edit_text(
        text=(
            "<b>➕ Новая задача</b>\n\n"
            "Введите название задачи:"
        ),
        reply_markup=get_cancel_button()
    )
    await callback.answer()


@router.message(TaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext) -> None:
    """Process task title"""
    title = message.text.strip()
    await message.delete()
    
    if len(title) < 3:
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новая задача</b>\n\n"
                    "❌ Название слишком короткое. Минимум 3 символа.\n\n"
                    "Введите название задачи:"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    if len(title) > 200:
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новая задача</b>\n\n"
                    "❌ Название слишком длинное. Максимум 200 символов.\n\n"
                    "Введите название задачи:"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    await state.update_data(title=title)
    await state.set_state(TaskStates.waiting_for_description)
    
    data = await state.get_data()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["message_id"],
        text=(
            "<b>➕ Новая задача</b>\n\n"
            "Введите описание задачи или отправьте <code>-</code> для пропуска:"
        ),
        reply_markup=get_cancel_button()
    )


@router.message(TaskStates.waiting_for_description)
async def process_task_description(message: Message, state: FSMContext) -> None:
    """Process task description"""
    description = message.text.strip()
    await message.delete()
    
    if description == "-":
        description = ""
    
    if len(description) > 1000:
        data = await state.get_data()
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новая задача</b>\n\n"
                    "❌ Описание слишком длинное. Максимум 1000 символов.\n\n"
                    "Введите описание задачи или отправьте <code>-</code> для пропуска:"
                ),
                reply_markup=get_cancel_button()
            )
        except:
            pass
        return
    
    await state.update_data(description=description)
    await state.set_state(TaskStates.waiting_for_date)
    
    data = await state.get_data()
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data["message_id"],
        text=(
            "<b>➕ Новая задача</b>\n\n"
            "Введите дату и время выполнения в формате:\n"
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
            "Примеры:\n"
            "• <code>15.10.2025 14:30</code>\n"
            "• <code>20.12.2025 09:00</code>"
        ),
        reply_markup=get_cancel_button()
    )


@router.message(TaskStates.waiting_for_date)
async def process_task_date(
    message: Message,
    state: FSMContext,
    task_repo: TaskRepository
) -> None:
    """Process task date and create task"""
    date_str = message.text.strip()
    await message.delete()
    
    data = await state.get_data()
    
    try:
        due_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
        tz = ZoneInfo(settings.default_timezone)
        due_date = due_date.replace(tzinfo=tz)
        
        now = datetime.now(tz)
        if due_date <= now:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data["message_id"],
                text=(
                    "<b>➕ Новая задача</b>\n\n"
                    "❌ Дата должна быть в будущем.\n\n"
                    "Введите дату и время в формате:\n"
                    "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>"
                ),
                reply_markup=get_cancel_button()
            )
            return
        
        title = data["title"]
        description = data.get("description", "")
        
        task_id = await task_repo.create_task(
            user_id=message.from_user.id,
            title=title,
            description=description,
            due_date=due_date
        )
        
        await state.clear()
        
        formatted_date = due_date.strftime("%d.%m.%Y %H:%M")
        safe_title = escape_html(title)
        safe_description = escape_html(description) if description else "Не указано"
        
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["message_id"],
            text=(
                "<b>✅ Задача создана!</b>\n\n"
                f"<b>Название:</b> {safe_title}\n"
                f"<b>Описание:</b> {safe_description}\n"
                f"<b>Срок:</b> {formatted_date}"
            ),
            reply_markup=get_tasks_menu()
        )
        logger.info(f"Task {task_id} created by user {message.from_user.id}")
        
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data["message_id"],
            text=(
                "<b>➕ Новая задача</b>\n\n"
                "❌ Неверный формат даты.\n\n"
                "Используйте формат:\n"
                "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
                "Например: <code>15.10.2025 14:30</code>"
            ),
            reply_markup=get_cancel_button()
        )

@router.callback_query(F.data.startswith("task:page:"))
async def tasks_pagination(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Handle task list pagination"""
    page_str = callback.data.split(":")[-1]
    if page_str == "current":
        await callback.answer()
        return
    
    page = int(page_str)
    await show_tasks_page(callback, task_repo, page)


@router.callback_query(F.data.startswith("task:actions:"))
async def show_task_actions(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Show actions for specific task"""
    task_id = int(callback.data.split(":")[-1])
    task = await task_repo.get_task_by_id(task_id)
    
    if not task or task["user_id"] != callback.from_user.id:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    tz = ZoneInfo(settings.default_timezone)
    due_date = datetime.fromisoformat(task["due_date"]).replace(tzinfo=tz)
    now = datetime.now(tz)
    time_left = due_date - now
    
    if time_left.total_seconds() < 0:
        time_status = "🔴 Просрочено!"
    elif time_left.total_seconds() < 3600:
        time_status = f"🟡 Осталось {int(time_left.total_seconds() / 60)} минут"
    elif time_left.days == 0:
        hours = int(time_left.total_seconds() / 3600)
        time_status = f"🟡 Осталось {hours} часов"
    else:
        time_status = f"🟢 Осталось {time_left.days} дней"
    
    description = task["description"] if task["description"] else "Не указано"
    safe_title = escape_html(task["title"])
    safe_description = escape_html(description)
    
    text = f"<b>{safe_title}</b>\n\n"
    text += f"<b>Описание:</b> {safe_description}\n"
    text += f"<b>Срок:</b> {due_date.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"<b>Статус:</b> {time_status}"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_task_action_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data == "task:delete")
async def delete_task_start(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Start task deletion"""
    tasks = await task_repo.get_user_tasks(callback.from_user.id)
    
    if not tasks:
        await callback.answer("У вас нет задач", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    sorted_tasks = sorted(tasks, key=lambda x: x["due_date"])
    
    for task in sorted_tasks:
        due_date = datetime.fromisoformat(task["due_date"])
        title = task["title"][:30] + "..." if len(task["title"]) > 30 else task["title"]
        builder.button(
            text=f"{title} • {due_date.strftime('%d.%m %H:%M')}",
            callback_data=f"task:delete_confirm:{task['id']}"
        )
    
    builder.button(text="◀️ Назад", callback_data="menu:tasks")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text="<b>🗑 Удаление задачи</b>\n\nВыберите задачу для удаления:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:delete_confirm:"))
async def delete_task_confirm(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Confirm task deletion"""
    task_id = int(callback.data.split(":")[-1])
    task = await task_repo.get_task_by_id(task_id)
    
    if not task or task["user_id"] != callback.from_user.id:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    await task_repo.delete_task(task_id)
    safe_title = escape_html(task["title"])
    
    await callback.message.edit_text(
        text=f"✅ Задача <b>{safe_title}</b> удалена",
        reply_markup=get_tasks_menu()
    )
    await callback.answer("✅ Удалено!")
    logger.info(f"Task {task_id} deleted by user {callback.from_user.id}")


@router.callback_query(F.data.startswith("task:complete:"))
async def complete_task(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Mark task as completed"""
    task_id = int(callback.data.split(":")[-1])
    task = await task_repo.get_task_by_id(task_id)
    
    if not task or task["user_id"] != callback.from_user.id:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    await task_repo.complete_task(task_id)
    safe_title = escape_html(task["title"])
    
    await callback.message.edit_text(
        text=f"✅ Задача <b>{safe_title}</b> выполнена!",
        reply_markup=get_tasks_menu()
    )
    await callback.answer("✅ Выполнено!")
    logger.info(f"Task {task_id} completed by user {callback.from_user.id}")


@router.callback_query(F.data.startswith("task:postpone_menu:"))
async def show_postpone_menu(callback: CallbackQuery) -> None:
    """Show postpone options"""
    task_id = int(callback.data.split(":")[-1])
    
    await callback.message.edit_text(
        text="<b>⏰ Отложить задачу</b>\n\nНа сколько отложить?",
        reply_markup=get_postpone_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task:postpone:"))
async def postpone_task(
    callback: CallbackQuery,
    task_repo: TaskRepository
) -> None:
    """Postpone task"""
    parts = callback.data.split(":")
    task_id = int(parts[2])
    minutes = int(parts[3])
    
    task = await task_repo.get_task_by_id(task_id)
    
    if not task or task["user_id"] != callback.from_user.id:
        await callback.answer("❌ Задача не найдена", show_alert=True)
        return
    
    tz = ZoneInfo(settings.default_timezone)
    current_due = datetime.fromisoformat(task["due_date"]).replace(tzinfo=tz)
    new_due = current_due + timedelta(minutes=minutes)
    
    await task_repo.postpone_task(task_id, new_due)
    
    safe_title = escape_html(task["title"])
    await callback.message.edit_text(
        text=(
            f"✅ Задача <b>{safe_title}</b> отложена\n\n"
            f"Новый срок: {new_due.strftime('%d.%m.%Y %H:%M')}"
        ),
        reply_markup=get_tasks_menu()
    )
    await callback.answer("✅ Отложено!")
    logger.info(f"Task {task_id} postponed by {minutes} minutes")