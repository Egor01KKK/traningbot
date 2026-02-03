from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db import crud


@dataclass
class DailySummary:
    summary_date: date
    calories_eaten: int
    calories_burned: int
    calories_net: int
    target_calories: int | None
    delta: int | None
    percent_of_target: int | None
    workout_count: int
    water_ml: int | None
    sleep_hours: Decimal | None


async def get_daily_summary(
    session: AsyncSession,
    user_id: int,
    summary_date: date | None = None,
) -> DailySummary:
    """Get comprehensive daily summary for a user."""
    if summary_date is None:
        summary_date = date.today()

    calories_eaten = await crud.get_total_calories_for_date(
        session, user_id, summary_date
    )
    calories_burned = await crud.get_burned_calories_for_date(
        session, user_id, summary_date
    )
    workouts = await crud.get_workouts_for_date(session, user_id, summary_date)
    daily_log = await crud.get_daily_log(session, user_id, summary_date)
    targets = await crud.get_computed_targets(session, user_id)

    calories_net = calories_eaten - calories_burned

    target_calories = targets.target_calories if targets else None
    delta = None
    percent_of_target = None

    if target_calories:
        delta = calories_net - target_calories
        if target_calories > 0:
            percent_of_target = int((calories_net / target_calories) * 100)

    water_ml = daily_log.water_ml if daily_log else None
    sleep_hours = daily_log.sleep_hours if daily_log else None

    return DailySummary(
        summary_date=summary_date,
        calories_eaten=calories_eaten,
        calories_burned=calories_burned,
        calories_net=calories_net,
        target_calories=target_calories,
        delta=delta,
        percent_of_target=percent_of_target,
        workout_count=len(workouts),
        water_ml=water_ml,
        sleep_hours=sleep_hours,
    )


def get_daily_recommendation(summary: DailySummary) -> str:
    """Generate recommendation based on daily summary."""
    if summary.target_calories is None:
        return ""

    delta = summary.delta
    target = summary.target_calories

    if delta is None:
        return ""

    if summary.calories_eaten == 0:
        return "Ещё не записал калории сегодня. Не забудь внести приёмы пищи!"

    if delta < -500:
        deficit_pct = abs(delta) / target * 100
        return (
            f"Дефицит великоват ({abs(delta)} ккал, -{deficit_pct:.0f}%)! "
            "Можешь добавить перекус или съесть что-то сытное. "
            "Большой дефицит мешает восстановлению."
        )
    elif delta < -200:
        return (
            "Небольшой дефицит — это нормально для похудения. "
            "Если чувствуешь голод, можно добавить белковый перекус."
        )
    elif delta < 0:
        return "Практически по плану! Так держать."
    elif delta < 200:
        return "Чуть выше плана, но в пределах нормы. Ничего страшного."
    elif delta < 500:
        return (
            "Профицит ~200-500 ккал. Если это не планово — "
            "завтра постарайся быть внимательнее к порциям."
        )
    else:
        return (
            f"Профицит {delta} ккал — многовато. "
            "Не ругай себя, но завтра постарайся вернуться к плану."
        )


def get_tomorrow_tip(summary: DailySummary) -> str:
    """Generate tip for tomorrow based on today's results."""
    if summary.target_calories is None:
        return ""

    if summary.calories_eaten == 0:
        return "На завтра: Записывай калории по ходу дня — так проще контролировать."

    delta = summary.delta
    if delta is None:
        return ""

    if delta < -300:
        return "На завтра: Попробуй приблизиться к плану. Регулярный дефицит замедляет метаболизм."
    elif delta > 300:
        return "На завтра: Сфокусируйся на белке и овощах — они дают сытость без лишних калорий."
    else:
        return "На завтра: Продолжай в том же духе!"
