from datetime import date
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.states import StrengthStates
from bot.services.calculator import calculate_e1rm
from bot.services.analytics import get_exercise_progress
from bot.utils.plotting import create_exercise_progress_chart
from bot.keyboards.reply import get_strength_keyboard, get_main_menu_keyboard
from bot.keyboards.inline import get_exercises_keyboard

router = Router()


@router.message(F.text == "➕ Добавить запись")
async def start_strength_log(message: Message, state: FSMContext):
    """Start adding strength log entry."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        exercises = await crud.get_user_exercises(session, user.id)

    if exercises:
        await message.answer(
            "Какое упражнение?",
            reply_markup=get_exercises_keyboard(exercises),
        )
    else:
        await message.answer("Какое упражнение? (напиши название)")
        await state.set_state(StrengthStates.waiting_for_exercise_name)


@router.callback_query(F.data.startswith("exercise_"))
async def select_exercise(callback: CallbackQuery, state: FSMContext):
    """Handle exercise selection from keyboard."""
    exercise_data = callback.data.replace("exercise_", "")

    if exercise_data == "other":
        await callback.message.answer("Напиши название упражнения:")
        await state.set_state(StrengthStates.waiting_for_exercise_name)
    else:
        await state.update_data(exercise_name=exercise_data)
        await callback.message.answer("Вес? (кг)")
        await state.set_state(StrengthStates.waiting_for_weight)

    await callback.answer()


@router.message(StrengthStates.waiting_for_exercise_name)
async def process_exercise_name(message: Message, state: FSMContext):
    """Process exercise name input."""
    exercise_name = message.text.strip()
    if len(exercise_name) > 100:
        await message.answer("Название слишком длинное (макс. 100 символов):")
        return

    await state.update_data(exercise_name=exercise_name)
    await message.answer("Вес? (кг)")
    await state.set_state(StrengthStates.waiting_for_weight)


@router.message(StrengthStates.waiting_for_weight)
async def process_strength_weight(message: Message, state: FSMContext):
    """Process weight input."""
    try:
        weight = float(message.text.strip().replace(",", "."))
        if not 0 <= weight <= 500:
            await message.answer("Введи вес от 0 до 500 кг:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(weight_kg=Decimal(str(weight)))
    await message.answer("Повторы?")
    await state.set_state(StrengthStates.waiting_for_reps)


@router.message(StrengthStates.waiting_for_reps)
async def process_reps(message: Message, state: FSMContext):
    """Process reps input."""
    try:
        reps = int(message.text.strip())
        if not 1 <= reps <= 100:
            await message.answer("Введи повторы от 1 до 100:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    await state.update_data(reps=reps)
    await message.answer("Подходов?")
    await state.set_state(StrengthStates.waiting_for_sets)


@router.message(StrengthStates.waiting_for_sets)
async def process_sets(message: Message, state: FSMContext):
    """Process sets input and save entry."""
    try:
        sets = int(message.text.strip())
        if not 1 <= sets <= 50:
            await message.answer("Введи подходы от 1 до 50:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    data = await state.get_data()
    today = date.today()

    weight_kg = data["weight_kg"]
    reps = data["reps"]
    e1rm = calculate_e1rm(weight_kg, reps)

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        last_log = await crud.get_last_strength_log_for_exercise(
            session, user.id, data["exercise_name"]
        )

        await crud.create_strength_log(
            session,
            user.id,
            today,
            exercise_name=data["exercise_name"],
            weight_kg=weight_kg,
            reps=reps,
            sets=sets,
            e1rm=e1rm,
        )

    response = (
        f"Записал! {data['exercise_name']}: {weight_kg}кг × {reps} × {sets}\n"
        f"e1RM: ~{e1rm:.0f} кг"
    )

    if last_log and last_log.e1rm:
        diff = e1rm - last_log.e1rm
        if diff > 0:
            response += f" (+{diff:.0f} кг к прошлому разу) 📈"
        elif diff < 0:
            response += f" ({diff:.0f} кг)"

    await message.answer(response, reply_markup=get_strength_keyboard())
    await state.clear()


@router.message(F.text == "📈 Прогресс по упражнению")
async def start_progress_view(message: Message, state: FSMContext):
    """Start viewing exercise progress."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        exercises = await crud.get_user_exercises(session, user.id)

    if not exercises:
        await message.answer(
            "Пока нет записей. Добавь первую тренировку!",
            reply_markup=get_strength_keyboard(),
        )
        return

    await state.set_state(StrengthStates.waiting_for_exercise_progress)
    await message.answer(
        "По какому упражнению?",
        reply_markup=get_exercises_keyboard(exercises),
    )


@router.callback_query(
    F.data.startswith("exercise_"),
    StrengthStates.waiting_for_exercise_progress,
)
async def show_exercise_progress(callback: CallbackQuery, state: FSMContext):
    """Show progress chart for selected exercise."""
    exercise_data = callback.data.replace("exercise_", "")

    if exercise_data == "other":
        await callback.message.answer("Выбери упражнение из списка.")
        await callback.answer()
        return

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer("Ошибка. Попробуй /start")
            await state.clear()
            await callback.answer()
            return

        progress = await get_exercise_progress(session, user.id, exercise_data)

    if not progress or len(progress.dates) < 2:
        await callback.message.answer(
            f"Недостаточно данных по {exercise_data}. Нужно минимум 2 записи.",
            reply_markup=get_strength_keyboard(),
        )
        await state.clear()
        await callback.answer()
        return

    chart = create_exercise_progress_chart(progress)
    photo = BufferedInputFile(chart, filename="progress.png")

    await callback.message.answer_photo(photo)

    stats_text = (
        f"📊 {progress.exercise_name} за последние 8 недель:\n"
        f"• Макс. вес: {progress.initial_weight:.0f} кг → {progress.max_weight:.0f} кг "
        f"({progress.weight_change_pct:+.1f}%)\n"
        f"• e1RM: {progress.initial_e1rm:.0f} кг → {progress.max_e1rm:.0f} кг "
        f"({progress.e1rm_change_pct:+.1f}%)"
    )

    if progress.e1rm_change_pct > 5:
        stats_text += "\nСтабильный рост, держи темп! 💪"
    elif progress.e1rm_change_pct > 0:
        stats_text += "\nЕсть прогресс, продолжай!"

    await callback.message.answer(stats_text, reply_markup=get_strength_keyboard())
    await state.clear()
    await callback.answer()
