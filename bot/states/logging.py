from aiogram.fsm.state import State, StatesGroup


class LoggingStates(StatesGroup):
    """States for daily logging."""

    waiting_for_weight = State()
    waiting_for_calories = State()
    waiting_for_water = State()
    waiting_for_sleep = State()
