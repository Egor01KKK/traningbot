import logging
from typing import Optional

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from bot.config import config
from bot.services.analytics import WeeklyStats

logger = logging.getLogger(__name__)


async def get_coach_comment(stats: WeeklyStats, use_ai: bool = True) -> Optional[str]:
    """
    Generate AI coach comment for weekly report.

    Returns None if AI is disabled or unavailable.
    """
    if not OPENAI_AVAILABLE or not use_ai or not config.openai.api_key:
        return None

    try:
        client = AsyncOpenAI(api_key=config.openai.api_key)

        prompt = _build_prompt(stats)

        response = await client.chat.completions.create(
            model=config.openai.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — фитнес-коуч бот. Твоя задача — дать короткий, "
                        "мотивирующий комментарий к недельному отчёту пользователя. "
                        "Пиши на русском языке, дружелюбно но без лишних эмоций. "
                        "Будь конкретен — давай actionable советы. "
                        "Ответ должен быть 2-4 предложения, не больше."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.warning(f"Failed to get AI coach comment: {e}")
        return None


def _build_prompt(stats: WeeklyStats) -> str:
    """Build prompt from weekly stats."""
    parts = [f"Недельный отчёт пользователя ({stats.start_date} - {stats.end_date}):"]

    if stats.start_weight and stats.end_weight:
        parts.append(
            f"- Вес: {stats.start_weight:.1f} → {stats.end_weight:.1f} кг "
            f"({stats.weight_change:+.1f} кг, {stats.weight_change_pct:+.1f}%)"
        )

    if stats.avg_calories and stats.target_calories:
        parts.append(
            f"- Калории: в среднем {stats.avg_calories}/день (план {stats.target_calories})"
        )
        if stats.calories_deficit:
            parts.append(f"- Дефицит за неделю: {stats.calories_deficit} ккал")

    if stats.avg_water_ml:
        parts.append(f"- Вода: в среднем {stats.avg_water_ml / 1000:.1f}л/день")

    if stats.avg_sleep_hours:
        parts.append(f"- Сон: в среднем {stats.avg_sleep_hours:.1f} часа")

    parts.append(
        f"- Тренировки: {stats.workout_count} из {stats.planned_workouts} запланированных"
    )

    if stats.streak_weeks > 0:
        parts.append(f"- Streak: {stats.streak_weeks} недель подряд с тренировками")

    parts.append("\nДай короткий комментарий и один конкретный совет на следующую неделю.")

    return "\n".join(parts)
