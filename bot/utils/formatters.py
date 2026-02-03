from typing import Optional
from bot.services.calculator import NutritionTargets
from bot.services.analytics import WeeklyStats, MonthlyStats
from bot.services.alerts import Alert
from bot.services.daily_summary import DailySummary, get_daily_recommendation, get_tomorrow_tip


def format_targets(targets: NutritionTargets, weight_kg: float) -> str:
    """Format nutrition targets for display."""
    deficit_sign = "-" if targets.deficit_percent > 0 else "+"
    deficit_val = abs(targets.deficit_percent)

    return (
        "━━━━━━━━━━━━━━━━━━━\n"
        "📊 Твои расчёты:\n"
        f"• BMR: {targets.bmr} ккал\n"
        f"• TDEE: {targets.tdee} ккал\n"
        f"• Цель: {targets.target_calories} ккал/день ({deficit_sign}{deficit_val:.0f}%)\n\n"
        "🍽 Макросы на день:\n"
        f"• Белок: {targets.protein_g}г (2.0 г/кг)\n"
        f"• Жиры: {targets.fat_g}г (0.9 г/кг)\n"
        f"• Углеводы: {targets.carbs_g}г (остаток)\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ Это приблизительные расчёты. Через 2-3 недели скорректируем по факту."
    )


def format_weekly_report(stats: WeeklyStats, coach_comment: Optional[str] = None) -> str:
    """Format weekly report for display."""
    parts = [
        f"📊 Отчёт за неделю ({stats.start_date.strftime('%d.%m')} - {stats.end_date.strftime('%d.%m')}):",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    if stats.start_weight and stats.end_weight:
        change_str = f"{stats.weight_change:+.1f}" if stats.weight_change else "0"
        pct_str = f"{stats.weight_change_pct:+.1f}" if stats.weight_change_pct else "0"
        parts.append(
            f"⚖️ Вес: {stats.start_weight:.1f} → {stats.end_weight:.1f} кг "
            f"({change_str} кг, {pct_str}%)"
        )

    if stats.avg_calories:
        cal_str = f"🍽 Калории: в среднем {stats.avg_calories}/день"
        if stats.target_calories:
            cal_str += f" (план {stats.target_calories})"
        parts.append(cal_str)
        if stats.calories_deficit:
            parts.append(f"   Дефицит: ~{abs(stats.calories_deficit)} ккал за неделю")

    if stats.avg_water_ml:
        parts.append(f"💧 Вода: в среднем {stats.avg_water_ml / 1000:.1f}л/день")

    if stats.avg_sleep_hours:
        parts.append(f"😴 Сон: в среднем {stats.avg_sleep_hours:.1f} часа")

    parts.append(
        f"🏋️ Тренировки: {stats.workout_count} из {stats.planned_workouts} запланированных"
    )

    parts.append("━━━━━━━━━━━━━━━━━━━")

    if stats.streak_weeks > 0:
        parts.append(f"🔥 Streak: {stats.streak_weeks} недель подряд с тренировками!")

    if coach_comment:
        parts.append("")
        parts.append("🤖 Коуч говорит:")
        parts.append(f'"{coach_comment}"')

    return "\n".join(parts)


def format_monthly_report(stats: MonthlyStats) -> str:
    """Format monthly report for display."""
    parts = [
        f"📅 Сводка за месяц ({stats.start_date.strftime('%d.%m')} - {stats.end_date.strftime('%d.%m')}):",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    if stats.start_weight and stats.end_weight:
        change_str = f"{stats.weight_change:+.1f}" if stats.weight_change else "0"
        pct_str = f"{stats.weight_change_pct:+.1f}" if stats.weight_change_pct else "0"
        parts.append(
            f"⚖️ Вес: {stats.start_weight:.1f} → {stats.end_weight:.1f} кг "
            f"({change_str} кг, {pct_str}%)"
        )

    if stats.avg_calories:
        parts.append(f"🍽 Калории: в среднем {stats.avg_calories}/день")

    parts.append(f"🏋️ Всего тренировок: {stats.total_workouts}")
    parts.append(f"📈 Недель с данными: {stats.weeks_with_data} из 4")

    parts.append("━━━━━━━━━━━━━━━━━━━")

    return "\n".join(parts)


def format_alert(alert: Alert) -> str:
    """Format alert for display."""
    icons = {
        "rapid_weight_loss": "⚠️",
        "low_calories": "🤔",
        "missed_workouts": "💪",
    }
    icon = icons.get(alert.alert_type, "⚠️")

    return (
        f"{icon} {alert.title}!\n\n"
        f"{alert.message}\n\n"
        f"{alert.recommendation}"
    )


def format_daily_summary(summary: DailySummary, include_recommendation: bool = True) -> str:
    """Format daily summary for display."""
    date_str = summary.summary_date.strftime("%d.%m.%Y")

    parts = [
        f"📊 Итоги за {date_str}:",
        "━━━━━━━━━━━━━━━━━━━",
    ]

    parts.append(f"🍽 Съедено: {summary.calories_eaten} ккал")

    if summary.calories_burned > 0:
        parts.append(f"🔥 Сожжено: {summary.calories_burned} ккал")
        parts.append(f"📈 Нетто: {summary.calories_net} ккал")

    if summary.target_calories:
        parts.append(f"🎯 План: {summary.target_calories} ккал")

        if summary.delta is not None:
            if summary.delta >= 0:
                balance_str = f"+{summary.delta} ккал (профицит)"
            else:
                balance_str = f"{summary.delta} ккал (дефицит)"
            parts.append(f"📊 Баланс: {balance_str}")

    if summary.workout_count > 0:
        workout_word = "тренировка" if summary.workout_count == 1 else "тренировки"
        if summary.workout_count > 4:
            workout_word = "тренировок"
        parts.append(f"🏋️ Тренировок: {summary.workout_count}")

    if summary.water_ml:
        parts.append(f"💧 Вода: {summary.water_ml / 1000:.1f}л")

    if summary.sleep_hours:
        parts.append(f"😴 Сон: {summary.sleep_hours:.1f}ч")

    parts.append("━━━━━━━━━━━━━━━━━━━")

    if include_recommendation:
        recommendation = get_daily_recommendation(summary)
        if recommendation:
            parts.append("")
            parts.append(f"💡 {recommendation}")

        tip = get_tomorrow_tip(summary)
        if tip:
            parts.append("")
            parts.append(f"🌅 {tip}")

    return "\n".join(parts)


def format_calorie_entry_response(
    calories: int,
    total_today: int,
    target: Optional[int],
    burned: int = 0,
) -> str:
    """Format response after logging calories."""
    response = f"✅ +{calories} ккал записал!"

    if burned > 0:
        net = total_today - burned
        response += f"\n\n📊 Итого за день: {total_today} ккал"
        response += f"\n🔥 Сожжено: {burned} ккал"
        response += f"\n📈 Нетто: {net} ккал"
    else:
        response += f"\n\n📊 Итого за день: {total_today} ккал"

    if target:
        net = total_today - burned
        remaining = target - net
        if remaining > 0:
            response += f"\n\n🎯 План: {target} ккал"
            response += f"\n📌 Осталось: ~{remaining} ккал"
        elif remaining > -200:
            response += f"\n\n🎯 План: {target} ккал"
            response += "\n✅ Практически по плану!"
        else:
            response += f"\n\n🎯 План: {target} ккал"
            response += f"\n⚠️ Профицит: {abs(remaining)} ккал"

    return response


def format_workout_balance_response(
    workout_name: str,
    duration: int,
    calories_burned: int,
    calories_eaten: int,
    total_burned: int,
    target: Optional[int],
    workout_count: int,
) -> str:
    """Format response after logging workout with balance."""
    response = f"Записал! {workout_name} {duration} мин"
    if calories_burned > 0:
        response += f", ~{calories_burned} ккал"
    response += " 🔥"

    if workout_count > 0:
        response += f"\nЭто твоя {workout_count}-я тренировка на этой неделе."
        if workout_count >= 3:
            response += " Красавчик!"

    if calories_eaten > 0 or total_burned > 0:
        net = calories_eaten - total_burned
        response += f"\n\n📊 Баланс дня: {net} ккал (нетто)"

        if target:
            remaining = target - net
            if remaining > 0:
                response += f"\n📌 Осталось: ~{remaining} ккал до плана"
            else:
                response += f"\n✅ План выполнен (профицит {abs(remaining)} ккал)"

    return response


def format_plan_with_formulas(
    targets: NutritionTargets,
    weight_kg: float,
    height_cm: int,
    age: int,
    gender: str,
    activity_level: str,
) -> str:
    """Format plan explanation with formulas."""
    activity_names = {
        "sedentary": "сидячий",
        "light": "лёгкая активность",
        "moderate": "умеренная активность",
        "high": "высокая активность",
        "very_high": "очень высокая активность",
    }
    activity_factors = {
        "sedentary": "1.2",
        "light": "1.375",
        "moderate": "1.55",
        "high": "1.725",
        "very_high": "1.9",
    }
    activity_name = activity_names.get(activity_level, activity_level)
    activity_factor = activity_factors.get(activity_level, "1.55")

    gender_bonus = "+5" if gender == "male" else "-161"
    gender_name = "мужчина" if gender == "male" else "женщина"

    deficit_sign = "-" if targets.deficit_percent > 0 else "+"
    deficit_val = abs(float(targets.deficit_percent))

    return (
        "📐 Как это рассчитано:\n\n"
        f"1️⃣ BMR (базовый метаболизм): {targets.bmr} ккал\n"
        "   Формула Миффлина-Сан Жеора:\n"
        f"   10 × {weight_kg:.0f}кг + 6.25 × {height_cm}см - 5 × {age}лет {gender_bonus}\n\n"
        f"2️⃣ TDEE (с учётом активности): {targets.tdee} ккал\n"
        f"   BMR × {activity_factor} ({activity_name})\n\n"
        f"3️⃣ Цель: TDEE {deficit_sign} {deficit_val:.0f}% = {targets.target_calories} ккал\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📝 Расчёт макросов:\n\n"
        f"• Белок: 2г × {weight_kg:.0f}кг = {targets.protein_g}г\n"
        "  (сохранение мышц при дефиците)\n\n"
        f"• Жиры: 0.9г × {weight_kg:.0f}кг = {targets.fat_g}г\n"
        "  (минимум для гормонов)\n\n"
        f"• Углеводы: остаток = {targets.carbs_g}г\n"
        "  (целевые_ккал - белок×4 - жиры×9) / 4"
    )
