from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.states import OnboardingStates
from bot.keyboards.inline import (
    get_start_keyboard,
    get_gender_keyboard,
    get_activity_keyboard,
    get_goal_keyboard,
    get_goal_speed_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.services.calculator import calculate_targets
from bot.utils.formatters import format_targets

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    async with async_session() as session:
        user, created = await crud.get_or_create_user(
            session, message.from_user.id, message.from_user.username
        )

        profile = await crud.get_profile(session, user.id)

    if profile and profile.goal:
        await message.answer(
            "С возвращением! Выбери действие:",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()
    else:
        await message.answer(
            "Йо! Я твой фитнес-ассистент. Давай настроим профиль, "
            "чтобы я мог считать твои калории. Погнали?",
            reply_markup=get_start_keyboard(),
        )
        await state.set_state(OnboardingStates.waiting_for_start)


@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(callback: CallbackQuery, state: FSMContext):
    """Start the onboarding process."""
    await callback.message.edit_text(
        "Какой у тебя пол?",
        reply_markup=get_gender_keyboard(),
    )
    await state.set_state(OnboardingStates.waiting_for_gender)
    await callback.answer()


@router.callback_query(F.data.startswith("gender_"), OnboardingStates.waiting_for_gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Process gender selection."""
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)

    await callback.message.edit_text("Сколько тебе лет?")
    await state.set_state(OnboardingStates.waiting_for_age)
    await callback.answer()


@router.message(OnboardingStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    """Process age input."""
    try:
        age = int(message.text.strip())
        if not 14 <= age <= 100:
            await message.answer("Введи возраст от 14 до 100 лет:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(age=age)
    await message.answer("Какой рост? (см)")
    await state.set_state(OnboardingStates.waiting_for_height)


@router.message(OnboardingStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """Process height input."""
    try:
        height = int(message.text.strip())
        if not 100 <= height <= 250:
            await message.answer("Введи рост от 100 до 250 см:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(height_cm=height)
    await message.answer("Текущий вес? (кг)")
    await state.set_state(OnboardingStates.waiting_for_weight)


@router.message(OnboardingStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Process weight input."""
    try:
        weight = float(message.text.strip().replace(",", "."))
        if not 30 <= weight <= 300:
            await message.answer("Введи вес от 30 до 300 кг:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(current_weight_kg=Decimal(str(weight)))
    await message.answer(
        "Насколько ты активен?",
        reply_markup=get_activity_keyboard(),
    )
    await state.set_state(OnboardingStates.waiting_for_activity)


@router.callback_query(F.data.startswith("activity_"), OnboardingStates.waiting_for_activity)
async def process_activity(callback: CallbackQuery, state: FSMContext):
    """Process activity level selection."""
    activity = callback.data.split("_")[1]
    await state.update_data(activity_level=activity)

    await callback.message.edit_text(
        "Какая цель на ближайшие 4-8 недель?",
        reply_markup=get_goal_keyboard(),
    )
    await state.set_state(OnboardingStates.waiting_for_goal)
    await callback.answer()


@router.callback_query(F.data.startswith("goal_"), OnboardingStates.waiting_for_goal)
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Process goal selection."""
    goal = callback.data.split("_")[1]
    await state.update_data(goal=goal)

    await callback.message.edit_text(
        "Как быстро хочешь двигаться?",
        reply_markup=get_goal_speed_keyboard(),
    )
    await state.set_state(OnboardingStates.waiting_for_speed)
    await callback.answer()


@router.callback_query(F.data.startswith("speed_"), OnboardingStates.waiting_for_speed)
async def process_speed(callback: CallbackQuery, state: FSMContext):
    """Process goal speed selection and finish onboarding."""
    speed = callback.data.split("_")[1]
    await state.update_data(goal_speed=speed)

    data = await state.get_data()

    targets = calculate_targets(
        gender=data["gender"],
        weight_kg=data["current_weight_kg"],
        height_cm=data["height_cm"],
        age=data["age"],
        activity_level=data["activity_level"],
        goal=data["goal"],
        goal_speed=data["goal_speed"],
    )

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)

        await crud.create_or_update_profile(
            session,
            user.id,
            gender=data["gender"],
            age=data["age"],
            height_cm=data["height_cm"],
            current_weight_kg=data["current_weight_kg"],
            activity_level=data["activity_level"],
            goal=data["goal"],
            goal_speed=data["goal_speed"],
        )

        await crud.create_or_update_computed_targets(
            session,
            user.id,
            bmr=targets.bmr,
            tdee=targets.tdee,
            target_calories=targets.target_calories,
            protein_g=targets.protein_g,
            fat_g=targets.fat_g,
            carbs_g=targets.carbs_g,
            deficit_percent=targets.deficit_percent,
        )

        await crud.create_or_update_settings(session, user.id)

    formatted = format_targets(targets, float(data["current_weight_kg"]))
    await callback.message.edit_text(f"Готово! Вот твой план:\n\n{formatted}")

    await callback.message.answer(
        "Теперь можем начинать! Выбери действие:",
        reply_markup=get_main_menu_keyboard(),
    )

    await state.clear()
    await callback.answer()
