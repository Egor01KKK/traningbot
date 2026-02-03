from datetime import date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.states import WorkoutStates
from bot.keyboards.reply import get_workout_type_keyboard, get_main_menu_keyboard

router = Router()

WORKOUT_TYPES = {
    "🏋️ Зал": "gym",
    "🏃 Кардио": "cardio",
    "🚶 Ходьба": "walking",
    "🎯 Другое": "other",
}


@router.message(F.text.in_(WORKOUT_TYPES.keys()))
async def select_workout_type(message: Message, state: FSMContext):
    """Handle workout type selection."""
    workout_type = WORKOUT_TYPES[message.text]
    await state.update_data(workout_type=workout_type)

    await message.answer("Сколько минут?")
    await state.set_state(WorkoutStates.waiting_for_duration)


@router.message(WorkoutStates.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    """Process workout duration."""
    try:
        duration = int(message.text.strip())
        if not 1 <= duration <= 480:
            await message.answer("Введи длительность от 1 до 480 минут:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(duration_min=duration)
    await message.answer("Примерно сколько сжёг? (ккал, можно 0 если не знаешь)")
    await state.set_state(WorkoutStates.waiting_for_calories)


@router.message(WorkoutStates.waiting_for_calories)
async def process_workout_calories(message: Message, state: FSMContext):
    """Process calories burned and save workout."""
    try:
        calories = int(message.text.strip())
        if not 0 <= calories <= 5000:
            await message.answer("Введи калории от 0 до 5000:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    data = await state.get_data()
    today = date.today()

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        await crud.create_workout(
            session,
            user.id,
            today,
            workout_type=data["workout_type"],
            duration_min=data["duration_min"],
            calories_burned=calories if calories > 0 else None,
        )

        week_count = await crud.get_workouts_count_this_week(session, user.id, today)

    workout_names = {
        "gym": "Зал",
        "cardio": "Кардио",
        "walking": "Ходьба",
        "other": "Тренировка",
    }
    workout_name = workout_names.get(data["workout_type"], "Тренировка")

    response = f"Записал! {workout_name} {data['duration_min']} мин"
    if calories > 0:
        response += f", ~{calories} ккал"
    response += " 🔥"

    if week_count > 0:
        response += f"\nЭто твоя {week_count}-я тренировка на этой неделе."
        if week_count >= 3:
            response += " Красавчик!"

    await message.answer(response, reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "alert_log_workout")
async def callback_log_workout(callback: CallbackQuery, state: FSMContext):
    """Handle workout logging callback from alert."""
    await callback.message.answer(
        "Какая тренировка?",
        reply_markup=get_workout_type_keyboard(),
    )
    await callback.answer()
