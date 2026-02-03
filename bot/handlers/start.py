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
    get_back_to_start_keyboard,
    get_gender_keyboard,
    get_activity_keyboard,
    get_goal_keyboard,
    get_goal_speed_keyboard,
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.services.calculator import calculate_targets
from bot.utils.formatters import format_targets

router = Router()

WELCOME_TEXT = (
    "👋 Йо! Я *Качалочкин* — твой фитнес-ассистент.\n\n"
    "Помогу отслеживать питание, тренировки и прогресс. "
    "Давай настроим профиль, чтобы я мог считать твои калории!"
)

FEATURES_TEXT = (
    "🎯 *Что умеет бот:*\n\n"
    "📊 *Расчёт калорий и макросов*\n"
    "Персональный план на основе твоих данных (BMR, TDEE)\n\n"
    "🍽 *Учёт питания*\n"
    "Записывай калории несколько раз в день — они накапливаются\n\n"
    "🏋️ *Тренировки*\n"
    "Записывай тренировки и сожжённые калории\n\n"
    "💪 *Силовой журнал*\n"
    "Отслеживай прогресс в упражнениях (e1RM)\n\n"
    "📈 *Отчёты и графики*\n"
    "Недельные/месячные отчёты, график веса\n\n"
    "🔔 *Умные напоминания*\n"
    "Вечерняя сводка с рекомендациями\n\n"
    "⚠️ *Алерты*\n"
    "Предупреждения о слишком быстром похудении или низких калориях"
)

HOWTO_TEXT = (
    "📖 *Как пользоваться:*\n\n"
    "*1. Настрой профиль*\n"
    "Укажи пол, возраст, рост, вес, активность и цель. "
    "Бот рассчитает твой план калорий и БЖУ.\n\n"
    "*2. Записывай данные*\n"
    "• 🍽 Калории — можно несколько раз в день\n"
    "• ⚖️ Вес — лучше раз в неделю утром\n"
    "• 💧 Вода и 😴 сон — по желанию\n\n"
    "*3. Отмечай тренировки*\n"
    "Тип, длительность, сожжённые калории.\n\n"
    "*4. Смотри итоги*\n"
    "Кнопка «📊 Итоги сегодня» покажет баланс:\n"
    "съедено - сожжено = нетто калорий\n\n"
    "*5. Анализируй прогресс*\n"
    "Недельные отчёты покажут тренд веса и соблюдение плана.\n\n"
    "💡 *Совет:* Записывай калории сразу после еды — так проще!"
)


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
            WELCOME_TEXT,
            reply_markup=get_start_keyboard(),
            parse_mode="Markdown",
        )
        await state.set_state(OnboardingStates.waiting_for_start)


@router.callback_query(F.data == "info_features")
async def show_features(callback: CallbackQuery, state: FSMContext):
    """Show bot features."""
    await callback.message.edit_text(
        FEATURES_TEXT,
        reply_markup=get_back_to_start_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "info_howto")
async def show_howto(callback: CallbackQuery, state: FSMContext):
    """Show how to use the bot."""
    await callback.message.edit_text(
        HOWTO_TEXT,
        reply_markup=get_back_to_start_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    """Go back to start screen."""
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


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
