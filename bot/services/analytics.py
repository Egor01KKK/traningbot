from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db import crud


@dataclass
class WeeklyStats:
    start_date: date
    end_date: date
    start_weight: Optional[Decimal]
    end_weight: Optional[Decimal]
    weight_change: Optional[Decimal]
    weight_change_pct: Optional[Decimal]
    avg_calories: Optional[int]
    target_calories: Optional[int]
    calories_deficit: Optional[int]
    avg_water_ml: Optional[int]
    avg_sleep_hours: Optional[Decimal]
    workout_count: int
    planned_workouts: int
    streak_weeks: int


@dataclass
class MonthlyStats:
    start_date: date
    end_date: date
    start_weight: Optional[Decimal]
    end_weight: Optional[Decimal]
    weight_change: Optional[Decimal]
    weight_change_pct: Optional[Decimal]
    avg_calories: Optional[int]
    total_workouts: int
    weeks_with_data: int


@dataclass
class WeightTrend:
    dates: list[date]
    weights: list[Decimal]
    moving_avg: list[Decimal]


@dataclass
class ExerciseProgress:
    exercise_name: str
    dates: list[date]
    weights: list[Decimal]
    e1rms: list[Decimal]
    max_weight: Decimal
    max_e1rm: Decimal
    initial_weight: Decimal
    initial_e1rm: Decimal
    weight_change_pct: Decimal
    e1rm_change_pct: Decimal


async def get_weekly_stats(
    session: AsyncSession,
    user_id: int,
    end_date: Optional[date] = None,
) -> WeeklyStats:
    """Get statistics for the week ending on end_date."""
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=6)

    daily_logs = await crud.get_daily_logs_range(session, user_id, start_date, end_date)
    workouts = await crud.get_workouts_range(session, user_id, start_date, end_date)
    targets = await crud.get_computed_targets(session, user_id)
    streak = await crud.get_workout_streak(session, user_id)

    weights = [log.weight_kg for log in daily_logs if log.weight_kg is not None]
    calories = [log.calories_consumed for log in daily_logs if log.calories_consumed is not None]
    water = [log.water_ml for log in daily_logs if log.water_ml is not None]
    sleep = [log.sleep_hours for log in daily_logs if log.sleep_hours is not None]

    start_weight = weights[0] if weights else None
    end_weight = weights[-1] if weights else None

    weight_change = None
    weight_change_pct = None
    if start_weight and end_weight:
        weight_change = end_weight - start_weight
        weight_change_pct = (weight_change / start_weight) * 100

    avg_calories = int(sum(calories) / len(calories)) if calories else None
    target_calories = targets.target_calories if targets else None

    calories_deficit = None
    if avg_calories and target_calories:
        calories_deficit = (target_calories - avg_calories) * len(calories)

    return WeeklyStats(
        start_date=start_date,
        end_date=end_date,
        start_weight=start_weight,
        end_weight=end_weight,
        weight_change=weight_change,
        weight_change_pct=weight_change_pct,
        avg_calories=avg_calories,
        target_calories=target_calories,
        calories_deficit=calories_deficit,
        avg_water_ml=int(sum(water) / len(water)) if water else None,
        avg_sleep_hours=sum(sleep, Decimal(0)) / len(sleep) if sleep else None,
        workout_count=len(workouts),
        planned_workouts=4,
        streak_weeks=streak,
    )


async def get_monthly_stats(
    session: AsyncSession,
    user_id: int,
    end_date: Optional[date] = None,
) -> MonthlyStats:
    """Get statistics for the month ending on end_date."""
    if end_date is None:
        end_date = date.today()

    start_date = end_date - timedelta(days=29)

    daily_logs = await crud.get_daily_logs_range(session, user_id, start_date, end_date)
    workouts = await crud.get_workouts_range(session, user_id, start_date, end_date)

    weights = [log.weight_kg for log in daily_logs if log.weight_kg is not None]
    calories = [log.calories_consumed for log in daily_logs if log.calories_consumed is not None]

    start_weight = weights[0] if weights else None
    end_weight = weights[-1] if weights else None

    weight_change = None
    weight_change_pct = None
    if start_weight and end_weight:
        weight_change = end_weight - start_weight
        weight_change_pct = (weight_change / start_weight) * 100

    weeks_with_data = 0
    for week in range(4):
        week_start = start_date + timedelta(days=week * 7)
        week_end = week_start + timedelta(days=6)
        week_logs = [
            log for log in daily_logs
            if week_start <= log.log_date <= week_end and log.weight_kg is not None
        ]
        if week_logs:
            weeks_with_data += 1

    return MonthlyStats(
        start_date=start_date,
        end_date=end_date,
        start_weight=start_weight,
        end_weight=end_weight,
        weight_change=weight_change,
        weight_change_pct=weight_change_pct,
        avg_calories=int(sum(calories) / len(calories)) if calories else None,
        total_workouts=len(workouts),
        weeks_with_data=weeks_with_data,
    )


async def get_weight_trend(
    session: AsyncSession,
    user_id: int,
    days: int = 30,
) -> WeightTrend:
    """Get weight data with moving average for charting."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    daily_logs = await crud.get_daily_logs_range(session, user_id, start_date, end_date)
    logs_with_weight = [log for log in daily_logs if log.weight_kg is not None]

    dates = [log.log_date for log in logs_with_weight]
    weights = [log.weight_kg for log in logs_with_weight]

    moving_avg = []
    window = 7
    for i, weight in enumerate(weights):
        start_idx = max(0, i - window + 1)
        window_weights = weights[start_idx : i + 1]
        avg = sum(window_weights, Decimal(0)) / len(window_weights)
        moving_avg.append(avg)

    return WeightTrend(dates=dates, weights=weights, moving_avg=moving_avg)


async def get_exercise_progress(
    session: AsyncSession,
    user_id: int,
    exercise_name: str,
    weeks: int = 8,
) -> Optional[ExerciseProgress]:
    """Get progress data for a specific exercise."""
    logs = await crud.get_strength_logs_by_exercise(
        session, user_id, exercise_name, limit=weeks * 3
    )

    if not logs:
        return None

    logs = list(reversed(logs))

    dates = [log.log_date for log in logs]
    weights = [log.weight_kg for log in logs]
    e1rms = [log.e1rm for log in logs]

    initial_weight = weights[0]
    max_weight = max(weights)
    initial_e1rm = e1rms[0]
    max_e1rm = max(e1rms)

    weight_change_pct = ((max_weight - initial_weight) / initial_weight) * 100 if initial_weight else Decimal(0)
    e1rm_change_pct = ((max_e1rm - initial_e1rm) / initial_e1rm) * 100 if initial_e1rm else Decimal(0)

    return ExerciseProgress(
        exercise_name=exercise_name,
        dates=dates,
        weights=weights,
        e1rms=e1rms,
        max_weight=max_weight,
        max_e1rm=max_e1rm,
        initial_weight=initial_weight,
        initial_e1rm=initial_e1rm,
        weight_change_pct=weight_change_pct,
        e1rm_change_pct=e1rm_change_pct,
    )
