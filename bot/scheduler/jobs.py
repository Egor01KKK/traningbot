import logging
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from bot.db.database import async_session
from bot.db import crud
from bot.services.analytics import get_weekly_stats
from bot.services.daily_summary import get_daily_summary
from bot.services.alerts import check_alerts
from bot.services.coach import get_coach_comment
from bot.utils.formatters import format_weekly_report, format_alert, format_daily_summary
from bot.keyboards.inline import get_reminder_keyboard, get_alert_keyboard
from bot.config import config

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=config.timezone)


async def send_weigh_reminder(bot: Bot):
    """Send weight reminder to users who have it scheduled now."""
    logger.info("Running weigh reminder job")

    async with async_session() as session:
        users_with_settings = await crud.get_all_users_with_settings(session)

    current_time = datetime.now().time()
    current_weekday = datetime.now().strftime("%A").lower()

    for user, settings in users_with_settings:
        if settings.weigh_day != current_weekday:
            continue

        if abs(
            settings.weigh_time.hour * 60 + settings.weigh_time.minute
            - current_time.hour * 60 - current_time.minute
        ) > 5:
            continue

        try:
            await bot.send_message(
                user.telegram_id,
                "Доброе утро! Пора взвеситься ⚖️\n"
                "Напиши вес или нажми кнопку",
                reply_markup=get_reminder_keyboard("weigh"),
            )
            logger.info(f"Sent weigh reminder to user {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send weigh reminder to {user.telegram_id}: {e}")


async def send_daily_reminder(bot: Bot):
    """Send smart daily summary to users who have it scheduled now."""
    logger.info("Running daily reminder job")

    async with async_session() as session:
        users_with_settings = await crud.get_all_users_with_settings(session)

    current_time = datetime.now().time()
    today = date.today()

    for user, settings in users_with_settings:
        if abs(
            settings.daily_reminder_time.hour * 60 + settings.daily_reminder_time.minute
            - current_time.hour * 60 - current_time.minute
        ) > 5:
            continue

        try:
            async with async_session() as summary_session:
                summary = await get_daily_summary(summary_session, user.id, today)

            if summary.calories_eaten > 0 or summary.workout_count > 0:
                formatted = format_daily_summary(summary, include_recommendation=True)
                await bot.send_message(user.telegram_id, formatted)
            else:
                await bot.send_message(
                    user.telegram_id,
                    "Как прошёл день? Запиши итоги:",
                    reply_markup=get_reminder_keyboard("daily"),
                )

            logger.info(f"Sent daily reminder to user {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send daily reminder to {user.telegram_id}: {e}")


async def send_weekly_report(bot: Bot):
    """Send weekly report to users who have it scheduled now."""
    logger.info("Running weekly report job")

    async with async_session() as session:
        users_with_settings = await crud.get_all_users_with_settings(session)

    current_time = datetime.now().time()
    current_weekday = datetime.now().strftime("%A").lower()

    for user, settings in users_with_settings:
        if settings.weigh_day != current_weekday:
            continue

        if abs(
            settings.weekly_report_time.hour * 60 + settings.weekly_report_time.minute
            - current_time.hour * 60 - current_time.minute
        ) > 5:
            continue

        try:
            async with async_session() as report_session:
                stats = await get_weekly_stats(report_session, user.id)

            coach_comment = await get_coach_comment(stats, use_ai=settings.use_ai_coach)
            report = format_weekly_report(stats, coach_comment)

            await bot.send_message(user.telegram_id, report)
            logger.info(f"Sent weekly report to user {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send weekly report to {user.telegram_id}: {e}")


async def check_and_send_alerts(bot: Bot):
    """Check for alerts and send them to users."""
    logger.info("Running alerts check job")

    async with async_session() as session:
        users_with_settings = await crud.get_all_users_with_settings(session)

    for user, settings in users_with_settings:
        try:
            async with async_session() as alert_session:
                alerts = await check_alerts(alert_session, user.id)

            for alert in alerts:
                await bot.send_message(
                    user.telegram_id,
                    format_alert(alert),
                    reply_markup=get_alert_keyboard(alert.alert_type),
                )
                logger.info(
                    f"Sent alert {alert.alert_type} to user {user.telegram_id}"
                )
        except Exception as e:
            logger.error(f"Failed to check/send alerts to {user.telegram_id}: {e}")


def setup_scheduler(bot: Bot):
    """Setup all scheduled jobs."""
    scheduler.add_job(
        send_weigh_reminder,
        CronTrigger(minute="*/30"),
        args=[bot],
        id="weigh_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        send_daily_reminder,
        CronTrigger(minute="*/30"),
        args=[bot],
        id="daily_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        send_weekly_report,
        CronTrigger(minute="*/30"),
        args=[bot],
        id="weekly_report",
        replace_existing=True,
    )

    scheduler.add_job(
        check_and_send_alerts,
        CronTrigger(hour="12"),
        args=[bot],
        id="alerts_check",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")
