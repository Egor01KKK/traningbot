from datetime import date
from decimal import Decimal
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.states import LoggingStates
from bot.keyboards.reply import get_logging_keyboard, get_main_menu_keyboard

router = Router()


@router.message(F.text == "⚖️ Вес")
async def start_weight_logging(message: Message, state: FSMContext):
    """Start weight logging."""
    await message.answer("Сколько показали весы? (кг)")
    await state.set_state(LoggingStates.waiting_for_weight)


@router.message(LoggingStates.waiting_for_weight)
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

    weight_decimal = Decimal(str(weight))
    today = date.today()

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        await crud.create_or_update_daily_log(
            session, user.id, today, weight_kg=weight_decimal
        )

        week_ago_log = await crud.get_weight_week_ago(session, user.id, today)

    response = f"Записал! {weight:.1f} кг"

    if week_ago_log and week_ago_log.weight_kg:
        diff = weight_decimal - week_ago_log.weight_kg
        response += f" ({diff:+.1f} кг за неделю)."

        if Decimal("-1") <= diff <= Decimal("-0.3"):
            response += "\nХороший темп, не торопись — мышцы скажут спасибо 💪"
        elif diff < Decimal("-1"):
            response += "\n⚠️ Быстро уходит. Не переусердствуй с дефицитом."
        elif diff > Decimal("0"):
            response += "\nНе страшно, это может быть вода. Смотрим тренд."
    else:
        response += "."

    await message.answer(response, reply_markup=get_logging_keyboard())
    await state.clear()


@router.message(F.text == "🍽 Калории")
async def start_calories_logging(message: Message, state: FSMContext):
    """Start calories logging."""
    await message.answer("Сколько калорий съел сегодня?")
    await state.set_state(LoggingStates.waiting_for_calories)


@router.message(LoggingStates.waiting_for_calories)
async def process_calories(message: Message, state: FSMContext):
    """Process calories input."""
    try:
        calories = int(message.text.strip())
        if not 0 <= calories <= 10000:
            await message.answer("Введи калории от 0 до 10000:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    today = date.today()

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        await crud.create_or_update_daily_log(
            session, user.id, today, calories_consumed=calories
        )

        targets = await crud.get_computed_targets(session, user.id)

    response = f"Записал! {calories} ккал"

    if targets and targets.target_calories:
        target = targets.target_calories
        diff = target - calories

        response += f" из {target} ккал."

        if diff > 0:
            response += f" Дефицит {diff} ккал — в рамках плана ✅"
        elif diff < -200:
            response += f" Профицит {abs(diff)} ккал — многовато 🤔"
        else:
            response += " Практически по плану ✅"
    else:
        response += "."

    await message.answer(response, reply_markup=get_logging_keyboard())
    await state.clear()


@router.message(F.text == "💧 Вода")
async def start_water_logging(message: Message, state: FSMContext):
    """Start water logging."""
    await message.answer("Сколько воды выпил? (мл или л, например: 2000 или 2л)")
    await state.set_state(LoggingStates.waiting_for_water)


@router.message(LoggingStates.waiting_for_water)
async def process_water(message: Message, state: FSMContext):
    """Process water input."""
    text = message.text.strip().lower().replace(",", ".")

    try:
        if "л" in text:
            liters = float(text.replace("л", "").strip())
            water_ml = int(liters * 1000)
        else:
            water_ml = int(float(text))

        if not 0 <= water_ml <= 10000:
            await message.answer("Введи количество от 0 до 10000 мл:")
            return
    except ValueError:
        await message.answer("Введи число (например: 2000 или 2л):")
        return

    today = date.today()

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        await crud.create_or_update_daily_log(
            session, user.id, today, water_ml=water_ml
        )

    liters_display = water_ml / 1000
    response = f"Записал! {liters_display:.1f}л воды"

    if water_ml >= 2000:
        response += " — отлично! 💧"
    elif water_ml >= 1500:
        response += " — неплохо, но можно больше."
    else:
        response += " — маловато, старайся пить больше."

    await message.answer(response, reply_markup=get_logging_keyboard())
    await state.clear()


@router.message(F.text == "😴 Сон")
async def start_sleep_logging(message: Message, state: FSMContext):
    """Start sleep logging."""
    await message.answer("Сколько часов спал? (например: 7 или 7.5)")
    await state.set_state(LoggingStates.waiting_for_sleep)


@router.message(LoggingStates.waiting_for_sleep)
async def process_sleep(message: Message, state: FSMContext):
    """Process sleep input."""
    try:
        hours = float(message.text.strip().replace(",", "."))
        if not 0 <= hours <= 24:
            await message.answer("Введи часы от 0 до 24:")
            return
    except ValueError:
        await message.answer("Введи число:")
        return

    today = date.today()
    sleep_decimal = Decimal(str(hours))

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            await state.clear()
            return

        await crud.create_or_update_daily_log(
            session, user.id, today, sleep_hours=sleep_decimal
        )

    response = f"Записал! {hours:.1f}ч сна"

    if hours >= 7:
        response += " — хорошо! 😴"
    elif hours >= 6:
        response += " — сойдёт, но лучше 7-8 часов."
    else:
        response += " — маловато. Сон важен для восстановления!"

    await message.answer(response, reply_markup=get_logging_keyboard())
    await state.clear()


@router.callback_query(F.data == "log_weight")
async def callback_log_weight(callback: CallbackQuery, state: FSMContext):
    """Handle weight logging callback from reminder."""
    await callback.message.answer("Сколько показали весы? (кг)")
    await state.set_state(LoggingStates.waiting_for_weight)
    await callback.answer()


@router.callback_query(F.data == "log_calories")
async def callback_log_calories(callback: CallbackQuery, state: FSMContext):
    """Handle calories logging callback from reminder."""
    await callback.message.answer("Сколько калорий съел сегодня?")
    await state.set_state(LoggingStates.waiting_for_calories)
    await callback.answer()


@router.callback_query(F.data == "log_water")
async def callback_log_water(callback: CallbackQuery, state: FSMContext):
    """Handle water logging callback from reminder."""
    await callback.message.answer("Сколько воды выпил? (мл или л)")
    await state.set_state(LoggingStates.waiting_for_water)
    await callback.answer()


@router.callback_query(F.data == "log_sleep")
async def callback_log_sleep(callback: CallbackQuery, state: FSMContext):
    """Handle sleep logging callback from reminder."""
    await callback.message.answer("Сколько часов спал?")
    await state.set_state(LoggingStates.waiting_for_sleep)
    await callback.answer()


@router.callback_query(F.data == "log_done")
async def callback_log_done(callback: CallbackQuery, state: FSMContext):
    """Handle done callback from reminder."""
    await callback.message.answer("Отлично! До завтра 👋", reply_markup=get_main_menu_keyboard())
    await callback.answer()
