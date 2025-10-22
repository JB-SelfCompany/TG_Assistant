"""User FSM states"""
from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    """States for task creation"""
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()


class BirthdayStates(StatesGroup):
    """States for birthday creation"""
    waiting_for_name = State()
    waiting_for_date = State()


class WeatherStates(StatesGroup):
    """States for weather settings"""
    waiting_for_city = State()


class SettingsStates(StatesGroup):
    """States for settings"""
    waiting_for_city = State()


class CurrencyStates(StatesGroup):
    """States for currency conversion"""
    waiting_for_conversion = State()


class PlacesStates(StatesGroup):
    """States for places search"""
    waiting_for_location = State()