from bot.services.calculator import NutritionTargets
from bot.services.analytics import WeeklyStats, MonthlyStats
from bot.services.alerts import Alert


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


def format_weekly_report(stats: WeeklyStats, coach_comment: str | None = None) -> str:
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
