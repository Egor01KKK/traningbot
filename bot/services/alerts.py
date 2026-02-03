from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db import crud


@dataclass
class Alert:
    alert_type: str
    title: str
    message: str
    recommendation: str


async def check_alerts(
    session: AsyncSession,
    user_id: int,
) -> list[Alert]:
    """Check for any alerts based on user data."""
    alerts = []

    settings = await crud.get_settings(session, user_id)
    targets = await crud.get_computed_targets(session, user_id)

    alert_rapid_weight_loss = await _check_rapid_weight_loss(
        session, user_id, settings.alert_weight_loss_pct if settings else Decimal("1.0")
    )
    if alert_rapid_weight_loss:
        alerts.append(alert_rapid_weight_loss)

    if targets:
        alert_low_calories = await _check_low_calories(
            session,
            user_id,
            targets.target_calories,
            settings.alert_low_calories_pct if settings else Decimal("0.7"),
        )
        if alert_low_calories:
            alerts.append(alert_low_calories)

    alert_missed_workouts = await _check_missed_workouts(session, user_id)
    if alert_missed_workouts:
        alerts.append(alert_missed_workouts)

    return alerts


async def _check_rapid_weight_loss(
    session: AsyncSession,
    user_id: int,
    threshold_pct: Decimal,
) -> Optional[Alert]:
    """Check if weight loss is too rapid."""
    today = date.today()
    current_log = await crud.get_last_weight_log(session, user_id)
    week_ago_log = await crud.get_weight_week_ago(session, user_id, today)

    if not current_log or not week_ago_log:
        return None

    current_weight = current_log.weight_kg
    week_ago_weight = week_ago_log.weight_kg

    if not current_weight or not week_ago_weight:
        return None

    weight_change = week_ago_weight - current_weight
    change_pct = (weight_change / week_ago_weight) * 100

    if change_pct > threshold_pct:
        return Alert(
            alert_type="rapid_weight_loss",
            title="Быстрый спад веса",
            message=(
                f"За неделю ты потерял {weight_change:.1f} кг ({change_pct:.1f}% от массы).\n"
                f"Это быстрее рекомендуемого темпа (0.5-1%)."
            ),
            recommendation=(
                "Риски: потеря мышц, замедление метаболизма.\n"
                "Рекомендация: добавь 150-200 ккал к дневной норме."
            ),
        )
    return None


async def _check_low_calories(
    session: AsyncSession,
    user_id: int,
    target_calories: int,
    threshold_pct: Decimal,
) -> Optional[Alert]:
    """Check if calories are consistently too low."""
    today = date.today()
    start_date = today - timedelta(days=2)

    logs = await crud.get_daily_logs_range(session, user_id, start_date, today)
    calories_logs = [log for log in logs if log.calories_consumed is not None]

    if len(calories_logs) < 3:
        return None

    threshold = int(target_calories * threshold_pct)
    low_days = sum(1 for log in calories_logs if log.calories_consumed < threshold)

    if low_days >= 3:
        avg_calories = sum(log.calories_consumed for log in calories_logs) // len(calories_logs)
        return Alert(
            alert_type="low_calories",
            title="Низкие калории",
            message=(
                f"Три дня подряд калории ниже {threshold}.\n"
                f"Твой план — {target_calories}. Это слишком большой дефицит."
            ),
            recommendation="Не голодай — это контрпродуктивно для рекомпозиции.",
        )
    return None


async def _check_missed_workouts(
    session: AsyncSession,
    user_id: int,
) -> Optional[Alert]:
    """Check if user has missed workouts for too long."""
    last_workout = await crud.get_last_workout(session, user_id)

    if not last_workout:
        return None

    days_since = (date.today() - last_workout.workout_date).days

    if days_since >= 5:
        return Alert(
            alert_type="missed_workouts",
            title="Пропуски тренировок",
            message=(
                f"Уже {days_since} дней без тренировки.\n"
                "Понимаю, бывает. Но давай не превращать это в привычку."
            ),
            recommendation=(
                "План на неделю:\n"
                "• Пн — зал (верх)\n"
                "• Ср — зал (низ)\n"
                "• Сб — кардио/ходьба 30 мин"
            ),
        )
    return None
