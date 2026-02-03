from aiogram.fsm.state import State, StatesGroup


class WorkoutStates(StatesGroup):
    """States for workout logging."""

    waiting_for_type = State()
    waiting_for_duration = State()
    waiting_for_calories = State()
