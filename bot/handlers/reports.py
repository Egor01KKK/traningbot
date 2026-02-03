from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from datetime import date

from bot.db.database import async_session
from bot.db import crud
from bot.services.analytics import get_weekly_stats, get_monthly_stats, get_weight_trend
from bot.services.daily_summary import get_daily_summary
from bot.services.coach import get_coach_comment
from bot.utils.plotting import create_weight_chart
from bot.utils.formatters import format_weekly_report, format_monthly_report, format_daily_summary
from bot.keyboards.reply import get_reports_keyboard, get_main_menu_keyboard

router = Router()


@router.message(F.text == "📊 Итоги сегодня")
async def show_today_summary(message: Message, state: FSMContext):
    """Show today's summary in one click."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        summary = await get_daily_summary(session, user.id, date.today())

    formatted = format_daily_summary(summary, include_recommendation=True)
    await message.answer(formatted, reply_markup=get_main_menu_keyboard())


@router.message(F.text == "📈 График веса")
async def show_weight_chart(message: Message, state: FSMContext):
    """Show weight trend chart."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        trend = await get_weight_trend(session, user.id, days=30)

    if len(trend.dates) < 2:
        await message.answer(
            "Недостаточно данных для графика. Записывай вес регулярно!",
            reply_markup=get_reports_keyboard(),
        )
        return

    chart = create_weight_chart(trend)
    photo = BufferedInputFile(chart, filename="weight_chart.png")

    await message.answer_photo(
        photo,
        caption="📈 Динамика веса за последние 30 дней",
    )
    await message.answer(
        "Синяя линия — скользящее среднее, оно показывает реальный тренд.",
        reply_markup=get_reports_keyboard(),
    )


@router.message(F.text == "📊 Недельный отчёт")
async def show_weekly_report(message: Message, state: FSMContext):
    """Show weekly report."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        stats = await get_weekly_stats(session, user.id)
        settings = await crud.get_settings(session, user.id)
        trend = await get_weight_trend(session, user.id, days=14)

    use_ai = settings.use_ai_coach if settings else True
    coach_comment = await get_coach_comment(stats, use_ai=use_ai)

    if len(trend.dates) >= 2:
        chart = create_weight_chart(trend)
        photo = BufferedInputFile(chart, filename="weekly_weight.png")
        await message.answer_photo(photo)

    report = format_weekly_report(stats, coach_comment)
    await message.answer(report, reply_markup=get_reports_keyboard())


@router.message(F.text == "📅 Месячная сводка")
async def show_monthly_report(message: Message, state: FSMContext):
    """Show monthly report."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        stats = await get_monthly_stats(session, user.id)
        trend = await get_weight_trend(session, user.id, days=30)

    if len(trend.dates) >= 2:
        chart = create_weight_chart(trend)
        photo = BufferedInputFile(chart, filename="monthly_weight.png")
        await message.answer_photo(photo)

    report = format_monthly_report(stats)
    await message.answer(report, reply_markup=get_reports_keyboard())


@router.message(F.text == "🔥 Streak")
async def show_streak(message: Message, state: FSMContext):
    """Show workout streak."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка. Попробуй /start")
            return

        streak = await crud.get_workout_streak(session, user.id)

    if streak == 0:
        response = (
            "🔥 Streak: 0 недель\n\n"
            "Пока нет серии. Запиши тренировку, чтобы начать!"
        )
    elif streak == 1:
        response = "🔥 Streak: 1 неделя\n\nНачало положено! Продолжай."
    else:
        response = f"🔥 Streak: {streak} недель подряд с тренировками!\n\n"
        if streak >= 4:
            response += "Впечатляет! Ты уже выработал привычку 💪"
        elif streak >= 2:
            response += "Хороший старт! Держи темп."

    await message.answer(response, reply_markup=get_reports_keyboard())
