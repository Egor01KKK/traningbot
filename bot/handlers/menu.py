from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.keyboards.reply import (
    get_main_menu_keyboard,
    get_logging_keyboard,
    get_workout_type_keyboard,
    get_strength_keyboard,
    get_reports_keyboard,
    get_settings_keyboard,
)
from bot.keyboards.inline import get_plan_keyboard
from bot.utils.formatters import format_targets, format_plan_with_formulas
from bot.services.calculator import NutritionTargets

router = Router()


@router.message(F.text == "◀️ Назад")
async def go_back(message: Message, state: FSMContext):
    """Return to main menu."""
    await state.clear()
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    """Cancel current action."""
    await state.clear()
    await message.answer(
        "Действие отменено. Главное меню:",
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text == "📝 Записать")
async def open_logging_menu(message: Message, state: FSMContext):
    """Open logging submenu."""
    await state.clear()
    await message.answer(
        "Что записываем?",
        reply_markup=get_logging_keyboard(),
    )


@router.message(F.text == "🏋️ Тренировка")
async def open_workout_menu(message: Message, state: FSMContext):
    """Open workout logging."""
    await state.clear()
    await message.answer(
        "Какая тренировка?",
        reply_markup=get_workout_type_keyboard(),
    )


@router.message(F.text == "💪 Силовой журнал")
async def open_strength_menu(message: Message, state: FSMContext):
    """Open strength journal."""
    await state.clear()
    await message.answer(
        "Что делаем?",
        reply_markup=get_strength_keyboard(),
    )


@router.message(F.text == "📈 Отчёты")
async def open_reports_menu(message: Message, state: FSMContext):
    """Open reports submenu."""
    await state.clear()
    await message.answer(
        "Какой отчёт?",
        reply_markup=get_reports_keyboard(),
    )


@router.message(F.text == "⚙️ Настройки")
async def open_settings_menu(message: Message, state: FSMContext):
    """Open settings submenu."""
    await state.clear()
    await message.answer(
        "Настройки:",
        reply_markup=get_settings_keyboard(),
    )


@router.message(F.text == "📋 Мой план")
async def show_plan(message: Message, state: FSMContext):
    """Show user's nutrition plan with formula explanation button."""
    await state.clear()

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала пройди настройку: /start")
            return

        targets = await crud.get_computed_targets(session, user.id)
        profile = await crud.get_profile(session, user.id)

    if not targets or not profile:
        await message.answer("Сначала пройди настройку: /start")
        return

    nutrition = NutritionTargets(
        bmr=targets.bmr,
        tdee=targets.tdee,
        target_calories=targets.target_calories,
        protein_g=targets.protein_g,
        fat_g=targets.fat_g,
        carbs_g=targets.carbs_g,
        deficit_percent=targets.deficit_percent,
    )

    formatted = format_targets(nutrition, float(profile.current_weight_kg))
    await message.answer(formatted, reply_markup=get_plan_keyboard())


@router.callback_query(F.data == "show_formulas")
async def show_formulas(callback: CallbackQuery):
    """Show detailed formula explanation."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Ошибка. Попробуй /start")
            return

        targets = await crud.get_computed_targets(session, user.id)
        profile = await crud.get_profile(session, user.id)

    if not targets or not profile:
        await callback.answer("Данные не найдены")
        return

    nutrition = NutritionTargets(
        bmr=targets.bmr,
        tdee=targets.tdee,
        target_calories=targets.target_calories,
        protein_g=targets.protein_g,
        fat_g=targets.fat_g,
        carbs_g=targets.carbs_g,
        deficit_percent=targets.deficit_percent,
    )

    formatted = format_plan_with_formulas(
        targets=nutrition,
        weight_kg=float(profile.current_weight_kg),
        height_cm=profile.height_cm,
        age=profile.age,
        gender=profile.gender,
        activity_level=profile.activity_level,
    )

    await callback.message.answer(formatted)
    await callback.answer()
