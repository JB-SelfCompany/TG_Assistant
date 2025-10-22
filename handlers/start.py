"""Start and help handlers"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from keyboards.menu import get_main_menu

router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Handler for /start command
    """
    await state.clear()
    
    welcome_text = (
        f"👋 Привет, <b>{message.from_user.full_name}</b>!\n\n"
        "Я многофункциональный бот-помощник. Могу помочь тебе:\n\n"
        "📋 Управлять задачами и напоминаниями\n"
        "🎂 Отслеживать дни рождения\n"
        "🌤 Проверять погоду\n"
        "💱 Конвертировать валюты\n"
        "📍 Находить ближайшие места\n\n"
        "Выбери нужную функцию из меню ниже:"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu()
    )
    
    logger.info(f"User {message.from_user.id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handler for /help command
    """
    help_text = (
        "<b>📖 Справка по использованию бота</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Показать это сообщение\n"
        "/menu - Открыть главное меню\n\n"
        "<b>Функции бота:</b>\n\n"
        "<b>📋 Задачи:</b>\n"
        "• Создание задач с напоминаниями\n"
        "• Управление списком задач\n"
        "• Отложить или завершить задачу\n\n"
        "<b>🎂 Дни рождения:</b>\n"
        "• Добавление дней рождения\n"
        "• Автоматические напоминания\n\n"
        "<b>🌤 Погода:</b>\n"
        "• Текущая погода\n"
        "• Прогноз на 5 дней\n\n"
        "<b>💱 Валюты:</b>\n"
        "• Актуальные курсы валют\n"
        "• Конвертация валют\n\n"
        "<b>📍 Места:</b>\n"
        "• Поиск ближайших аптек, магазинов\n"
        "• Построение маршрутов\n"
    )
    
    await message.answer(
        text=help_text,
        reply_markup=get_main_menu()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """
    Handler for /menu command
    """
    await state.clear()
    
    await message.answer(
        text="🏠 <b>Главное меню</b>\n\nВыберите нужную функцию:",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Return to main menu"""
    await state.clear()
    
    try:
        await callback.message.edit_text(
            text="<b>📱 Главное меню</b>\n\nВыберите раздел:",
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Cancel current operation
    """
    await state.clear()
    
    await callback.message.edit_text(
        text="❌ Операция отменена\n\n🏠 Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer("Операция отменена")