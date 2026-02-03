from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """States for user onboarding flow."""

    waiting_for_start = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_activity = State()
    waiting_for_goal = State()
    waiting_for_speed = State()
    confirm = State()
