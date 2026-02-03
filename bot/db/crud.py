from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import (
    User,
    Profile,
    ComputedTargets,
    DailyLog,
    Workout,
    StrengthLog,
    Settings,
    CalorieEntry,
)


# ========== User ==========
async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, telegram_id: int, username: str | None = None
) -> User:
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, username: str | None = None
) -> tuple[User, bool]:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        return user, False
    user = await create_user(session, telegram_id, username)
    return user, True


# ========== Profile ==========
async def get_profile(session: AsyncSession, user_id: int) -> Profile | None:
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def create_or_update_profile(
    session: AsyncSession,
    user_id: int,
    gender: str | None = None,
    age: int | None = None,
    height_cm: int | None = None,
    current_weight_kg: Decimal | None = None,
    activity_level: str | None = None,
    goal: str | None = None,
    goal_speed: str | None = None,
) -> Profile:
    profile = await get_profile(session, user_id)
    if not profile:
        profile = Profile(user_id=user_id)
        session.add(profile)

    if gender is not None:
        profile.gender = gender
    if age is not None:
        profile.age = age
    if height_cm is not None:
        profile.height_cm = height_cm
    if current_weight_kg is not None:
        profile.current_weight_kg = current_weight_kg
    if activity_level is not None:
        profile.activity_level = activity_level
    if goal is not None:
        profile.goal = goal
    if goal_speed is not None:
        profile.goal_speed = goal_speed

    profile.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(profile)
    return profile


# ========== Computed Targets ==========
async def get_computed_targets(session: AsyncSession, user_id: int) -> ComputedTargets | None:
    result = await session.execute(
        select(ComputedTargets).where(ComputedTargets.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_computed_targets(
    session: AsyncSession,
    user_id: int,
    bmr: int,
    tdee: int,
    target_calories: int,
    protein_g: int,
    fat_g: int,
    carbs_g: int,
    deficit_percent: Decimal,
) -> ComputedTargets:
    targets = await get_computed_targets(session, user_id)
    if not targets:
        targets = ComputedTargets(user_id=user_id)
        session.add(targets)

    targets.bmr = bmr
    targets.tdee = tdee
    targets.target_calories = target_calories
    targets.protein_g = protein_g
    targets.fat_g = fat_g
    targets.carbs_g = carbs_g
    targets.deficit_percent = deficit_percent
    targets.calculated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(targets)
    return targets


# ========== Daily Log ==========
async def get_daily_log(
    session: AsyncSession, user_id: int, log_date: date
) -> DailyLog | None:
    result = await session.execute(
        select(DailyLog).where(
            and_(DailyLog.user_id == user_id, DailyLog.log_date == log_date)
        )
    )
    return result.scalar_one_or_none()


async def create_or_update_daily_log(
    session: AsyncSession,
    user_id: int,
    log_date: date,
    weight_kg: Decimal | None = None,
    calories_consumed: int | None = None,
    water_ml: int | None = None,
    sleep_hours: Decimal | None = None,
    notes: str | None = None,
) -> DailyLog:
    log = await get_daily_log(session, user_id, log_date)
    if not log:
        log = DailyLog(user_id=user_id, log_date=log_date)
        session.add(log)

    if weight_kg is not None:
        log.weight_kg = weight_kg
    if calories_consumed is not None:
        log.calories_consumed = calories_consumed
    if water_ml is not None:
        log.water_ml = water_ml
    if sleep_hours is not None:
        log.sleep_hours = sleep_hours
    if notes is not None:
        log.notes = notes

    await session.commit()
    await session.refresh(log)
    return log


async def get_daily_logs_range(
    session: AsyncSession, user_id: int, start_date: date, end_date: date
) -> list[DailyLog]:
    result = await session.execute(
        select(DailyLog)
        .where(
            and_(
                DailyLog.user_id == user_id,
                DailyLog.log_date >= start_date,
                DailyLog.log_date <= end_date,
            )
        )
        .order_by(DailyLog.log_date)
    )
    return list(result.scalars().all())


async def get_last_weight_log(session: AsyncSession, user_id: int) -> DailyLog | None:
    result = await session.execute(
        select(DailyLog)
        .where(and_(DailyLog.user_id == user_id, DailyLog.weight_kg.isnot(None)))
        .order_by(DailyLog.log_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_weight_week_ago(
    session: AsyncSession, user_id: int, current_date: date
) -> DailyLog | None:
    week_ago = current_date - timedelta(days=7)
    result = await session.execute(
        select(DailyLog)
        .where(
            and_(
                DailyLog.user_id == user_id,
                DailyLog.weight_kg.isnot(None),
                DailyLog.log_date <= week_ago,
            )
        )
        .order_by(DailyLog.log_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ========== Calorie Entry ==========
async def create_calorie_entry(
    session: AsyncSession,
    user_id: int,
    entry_date: date,
    calories: int,
    description: str | None = None,
) -> CalorieEntry:
    entry = CalorieEntry(
        user_id=user_id,
        entry_date=entry_date,
        calories=calories,
        description=description,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def get_total_calories_for_date(
    session: AsyncSession, user_id: int, entry_date: date
) -> int:
    """Get total consumed calories for a specific date."""
    result = await session.execute(
        select(func.sum(CalorieEntry.calories)).where(
            and_(CalorieEntry.user_id == user_id, CalorieEntry.entry_date == entry_date)
        )
    )
    return result.scalar() or 0


async def get_calorie_entries_for_date(
    session: AsyncSession, user_id: int, entry_date: date
) -> list[CalorieEntry]:
    """Get all calorie entries for a specific date."""
    result = await session.execute(
        select(CalorieEntry)
        .where(
            and_(CalorieEntry.user_id == user_id, CalorieEntry.entry_date == entry_date)
        )
        .order_by(CalorieEntry.created_at)
    )
    return list(result.scalars().all())


# ========== Workout ==========
async def create_workout(
    session: AsyncSession,
    user_id: int,
    workout_date: date,
    workout_type: str,
    duration_min: int | None = None,
    calories_burned: int | None = None,
    notes: str | None = None,
) -> Workout:
    workout = Workout(
        user_id=user_id,
        workout_date=workout_date,
        workout_type=workout_type,
        duration_min=duration_min,
        calories_burned=calories_burned,
        notes=notes,
    )
    session.add(workout)
    await session.commit()
    await session.refresh(workout)
    return workout


async def get_workouts_range(
    session: AsyncSession, user_id: int, start_date: date, end_date: date
) -> list[Workout]:
    result = await session.execute(
        select(Workout)
        .where(
            and_(
                Workout.user_id == user_id,
                Workout.workout_date >= start_date,
                Workout.workout_date <= end_date,
            )
        )
        .order_by(Workout.workout_date)
    )
    return list(result.scalars().all())


async def get_workouts_count_this_week(
    session: AsyncSession, user_id: int, current_date: date
) -> int:
    start_of_week = current_date - timedelta(days=current_date.weekday())
    result = await session.execute(
        select(func.count(Workout.id)).where(
            and_(
                Workout.user_id == user_id,
                Workout.workout_date >= start_of_week,
                Workout.workout_date <= current_date,
            )
        )
    )
    return result.scalar() or 0


async def get_last_workout(session: AsyncSession, user_id: int) -> Workout | None:
    result = await session.execute(
        select(Workout)
        .where(Workout.user_id == user_id)
        .order_by(Workout.workout_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_workouts_for_date(
    session: AsyncSession, user_id: int, workout_date: date
) -> list[Workout]:
    """Get all workouts for a specific date."""
    result = await session.execute(
        select(Workout)
        .where(
            and_(Workout.user_id == user_id, Workout.workout_date == workout_date)
        )
        .order_by(Workout.created_at)
    )
    return list(result.scalars().all())


async def get_burned_calories_for_date(
    session: AsyncSession, user_id: int, workout_date: date
) -> int:
    """Get total burned calories for a specific date."""
    result = await session.execute(
        select(func.sum(Workout.calories_burned)).where(
            and_(Workout.user_id == user_id, Workout.workout_date == workout_date)
        )
    )
    return result.scalar() or 0


# ========== Strength Log ==========
async def create_strength_log(
    session: AsyncSession,
    user_id: int,
    log_date: date,
    exercise_name: str,
    weight_kg: Decimal,
    reps: int,
    sets: int,
    e1rm: Decimal,
    notes: str | None = None,
) -> StrengthLog:
    log = StrengthLog(
        user_id=user_id,
        log_date=log_date,
        exercise_name=exercise_name,
        weight_kg=weight_kg,
        reps=reps,
        sets=sets,
        e1rm=e1rm,
        notes=notes,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def get_strength_logs_by_exercise(
    session: AsyncSession, user_id: int, exercise_name: str, limit: int = 20
) -> list[StrengthLog]:
    result = await session.execute(
        select(StrengthLog)
        .where(
            and_(
                StrengthLog.user_id == user_id,
                StrengthLog.exercise_name == exercise_name,
            )
        )
        .order_by(StrengthLog.log_date.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_last_strength_log_for_exercise(
    session: AsyncSession, user_id: int, exercise_name: str
) -> StrengthLog | None:
    result = await session.execute(
        select(StrengthLog)
        .where(
            and_(
                StrengthLog.user_id == user_id,
                StrengthLog.exercise_name == exercise_name,
            )
        )
        .order_by(StrengthLog.log_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_user_exercises(session: AsyncSession, user_id: int, limit: int = 10) -> list[str]:
    result = await session.execute(
        select(StrengthLog.exercise_name)
        .where(StrengthLog.user_id == user_id)
        .group_by(StrengthLog.exercise_name)
        .order_by(func.max(StrengthLog.log_date).desc())
        .limit(limit)
    )
    return [row[0] for row in result.all()]


# ========== Settings ==========
async def get_settings(session: AsyncSession, user_id: int) -> Settings | None:
    result = await session.execute(
        select(Settings).where(Settings.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_settings(
    session: AsyncSession, user_id: int, **kwargs
) -> Settings:
    settings = await get_settings(session, user_id)
    if not settings:
        settings = Settings(user_id=user_id)
        session.add(settings)

    for key, value in kwargs.items():
        if hasattr(settings, key) and value is not None:
            setattr(settings, key, value)

    await session.commit()
    await session.refresh(settings)
    return settings


# ========== Analytics helpers ==========
async def get_workout_streak(session: AsyncSession, user_id: int) -> int:
    """Count consecutive weeks with at least one workout."""
    result = await session.execute(
        select(Workout.workout_date)
        .where(Workout.user_id == user_id)
        .order_by(Workout.workout_date.desc())
    )
    dates = [row[0] for row in result.all()]

    if not dates:
        return 0

    current_date = date.today()
    streak = 0

    for week_offset in range(52):
        week_start = current_date - timedelta(days=current_date.weekday() + 7 * week_offset)
        week_end = week_start + timedelta(days=6)

        has_workout = any(week_start <= d <= week_end for d in dates)
        if has_workout:
            streak += 1
        else:
            break

    return streak


async def get_all_users_with_settings(session: AsyncSession) -> list[tuple[User, Settings]]:
    """Get all active users with their settings for scheduler."""
    result = await session.execute(
        select(User, Settings)
        .join(Settings, User.id == Settings.user_id)
        .where(User.is_active == True)
    )
    return list(result.all())
