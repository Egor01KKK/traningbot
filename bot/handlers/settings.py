from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import async_session
from bot.db import crud
from bot.keyboards.reply import get_settings_keyboard, get_main_menu_keyboard
from bot.keyboards.inline import get_start_keyboard

router = Router()


@router.message(F.text == "👤 Обновить профиль")
async def update_profile(message: Message, state: FSMContext):
    """Start profile update."""
    await message.answer(
        "Чтобы обновить профиль, пройди настройку заново:",
        reply_markup=get_start_keyboard(),
    )


@router.message(F.text == "⏰ Время напоминаний")
async def show_reminder_times(message: Message, state: FSMContext):
    """Show current reminder times."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        settings = await crud.get_settings(session, user.id)

    if not settings:
        await message.answer(
            "Настройки не найдены. Попробуй /start",
            reply_markup=get_settings_keyboard(),
        )
        return

    days_ru = {
        "monday": "Понедельник",
        "tuesday": "Вторник",
        "wednesday": "Среда",
        "thursday": "Четверг",
        "friday": "Пятница",
        "saturday": "Суббота",
        "sunday": "Воскресенье",
    }

    weigh_day_ru = days_ru.get(settings.weigh_day, settings.weigh_day)

    response = (
        "⏰ Текущие настройки напоминаний:\n\n"
        f"• Взвешивание: {weigh_day_ru} в {settings.weigh_time.strftime('%H:%M')}\n"
        f"• Итоги дня: каждый день в {settings.daily_reminder_time.strftime('%H:%M')}\n"
        f"• Недельный отчёт: {weigh_day_ru} в {settings.weekly_report_time.strftime('%H:%M')}\n"
        f"• Часовой пояс: {settings.timezone}\n\n"
        "📝 Для изменения напиши время в формате:\n"
        "взвешивание 09:00\n"
        "итоги 22:00"
    )

    await message.answer(response, reply_markup=get_settings_keyboard())


@router.message(F.text.lower().startswith("взвешивание"))
async def set_weigh_time(message: Message, state: FSMContext):
    """Set weighing reminder time."""
    try:
        time_str = message.text.split()[1]
        hours, minutes = map(int, time_str.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except (IndexError, ValueError):
        await message.answer(
            "Неверный формат. Напиши: взвешивание 09:00",
            reply_markup=get_settings_keyboard(),
        )
        return

    from datetime import time

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        await crud.create_or_update_settings(
            session, user.id, weigh_time=time(hours, minutes)
        )

    await message.answer(
        f"Время взвешивания изменено на {time_str}",
        reply_markup=get_settings_keyboard(),
    )


@router.message(F.text.lower().startswith("итоги"))
async def set_daily_reminder_time(message: Message, state: FSMContext):
    """Set daily reminder time."""
    try:
        time_str = message.text.split()[1]
        hours, minutes = map(int, time_str.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except (IndexError, ValueError):
        await message.answer(
            "Неверный формат. Напиши: итоги 22:00",
            reply_markup=get_settings_keyboard(),
        )
        return

    from datetime import time

    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        await crud.create_or_update_settings(
            session, user.id, daily_reminder_time=time(hours, minutes)
        )

    await message.answer(
        f"Время напоминания изменено на {time_str}",
        reply_markup=get_settings_keyboard(),
    )


@router.message(F.text == "🤖 AI-коуч: вкл/выкл")
async def toggle_ai_coach(message: Message, state: FSMContext):
    """Toggle AI coach."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        settings = await crud.get_settings(session, user.id)
        current = settings.use_ai_coach if settings else True

        await crud.create_or_update_settings(session, user.id, use_ai_coach=not current)

    new_state = "включен" if not current else "выключен"
    await message.answer(
        f"🤖 AI-коуч {new_state}.\n\n"
        f"{'Теперь в недельных отчётах будут комментарии от AI.' if not current else 'Комментарии AI больше не будут показываться.'}",
        reply_markup=get_settings_keyboard(),
    )


@router.callback_query(F.data == "alert_ack")
async def alert_acknowledged(callback: CallbackQuery, state: FSMContext):
    """Handle alert acknowledgment."""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Понял!")


@router.callback_query(F.data == "alert_adjust")
async def alert_adjust_plan(callback: CallbackQuery, state: FSMContext):
    """Handle plan adjustment from alert."""
    await callback.message.answer(
        "Для корректировки плана обнови профиль в настройках.",
        reply_markup=get_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "alert_show_plan")
async def alert_show_plan(callback: CallbackQuery, state: FSMContext):
    """Show plan from alert."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.message.answer("Ошибка. Попробуй /start")
            await callback.answer()
            return

        targets = await crud.get_computed_targets(session, user.id)

    if not targets:
        await callback.message.answer("План не найден. Попробуй /start")
        await callback.answer()
        return

    response = (
        "📋 Твой план:\n\n"
        f"• Калории: {targets.target_calories} ккал/день\n"
        f"• Белок: {targets.protein_g}г\n"
        f"• Жиры: {targets.fat_g}г\n"
        f"• Углеводы: {targets.carbs_g}г"
    )

    await callback.message.answer(response, reply_markup=get_main_menu_keyboard())
    await callback.answer()
