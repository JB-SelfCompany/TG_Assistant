"""Currency handlers"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.menu import get_currency_menu, get_cancel_button
from services.currency_service import CurrencyService
from states.user_states import CurrencyStates

router = Router(name="currency")
logger = logging.getLogger(__name__)

currency_service = CurrencyService()

@router.callback_query(F.data == "menu:currency")
async def show_currency_menu(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Show currency rates immediately (UPDATED)"""
    await state.clear()
    
    # Immediately show currency rates instead of menu
    await show_currency_rates(callback)


async def show_currency_rates(callback: CallbackQuery) -> None:
    """Show currency rates"""
    rates = await currency_service.get_rates()
    
    if not rates:
        await callback.message.edit_text(
            text="❌ Не удалось получить данные о курсах валют.\nПопробуйте позже.",
            reply_markup=get_currency_menu()
        )
        await callback.answer()
        return
    
    text = currency_service.format_rates(rates)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_currency_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "currency:convert")
async def start_conversion(callback: CallbackQuery, state: FSMContext) -> None:
    """Start currency conversion"""
    await state.set_state(CurrencyStates.waiting_for_conversion)
    
    await callback.message.edit_text(
        text=(
            "🔄 Конвертация валют\n\n"
            "Введите данные в формате:\n"
            "`СУММА ИЗ_ВАЛЮТЫ В_ВАЛЮТУ`\n\n"
            "Примеры:\n"
            "• `100 USD RUB`\n"
            "• `50 EUR USD`\n"
            "• `1000 RUB EUR`\n\n"
            "Доступные валюты: USD, EUR, RUB, CNY, GBP, JPY, CHF, UAH и другие"
        ),
        reply_markup=get_cancel_button()
    )
    await callback.answer()


@router.message(CurrencyStates.waiting_for_conversion)
async def process_currency_conversion(message: Message, state: FSMContext) -> None:
    """Process currency conversion"""
    try:
        parts = message.text.strip().upper().split()
        
        if len(parts) != 3:
            await message.answer(
                "❌ Неверный формат.\n\n"
                "Используйте: <code>СУММА ИЗ_ВАЛЮТЫ В_ВАЛЮТУ</code>\n"
                "Например: <code>100 USD RUB</code>"
            )
            return
        
        amount_str, from_curr, to_curr = parts
        amount = float(amount_str.replace(",", "."))
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля")
            return
        
        # Convert
        result = await currency_service.convert(amount, from_curr, to_curr)
        
        if result is None:
            await message.answer(
                "❌ Не удалось выполнить конвертацию.\n"
                "Проверьте правильность кодов валют."
            )
            return
        
        await state.clear()
        
        # Get emoji for currencies
        emoji_map = {
            "USD": "💵", "EUR": "💶", "RUB": "₽",
            "CNY": "🇨🇳", "GBP": "💷", "JPY": "💴",
            "CHF": "🇨🇭", "UAH": "🇺🇦"
        }
        
        from_emoji = emoji_map.get(from_curr, "💰")
        to_emoji = emoji_map.get(to_curr, "💰")
        
        await message.answer(
            text=(
                "✅ <b>Результат конвертации</b>\n\n"
                f"{from_emoji} {amount:.2f} {from_curr} =\n"
                f"{to_emoji} {result:.2f} {to_curr}"
            ),
            reply_markup=get_currency_menu()
        )
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат числа.\n"
            "Используйте: <code>100 USD RUB</code>"
        )
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await message.answer(
            "❌ Произошла ошибка при конвертации",
            reply_markup=get_currency_menu()
        )
