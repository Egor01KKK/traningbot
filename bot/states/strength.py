from aiogram.fsm.state import State, StatesGroup


class StrengthStates(StatesGroup):
    """States for strength journal."""

    waiting_for_exercise = State()
    waiting_for_exercise_name = State()
    waiting_for_weight = State()
    waiting_for_reps = State()
    waiting_for_sets = State()
    waiting_for_exercise_progress = State()
