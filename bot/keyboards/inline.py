from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Start onboarding keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поехали!", callback_data="start_onboarding")],
        ]
    )


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Gender selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужской", callback_data="gender_male"),
                InlineKeyboardButton(text="Женский", callback_data="gender_female"),
            ],
        ]
    )


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Activity level selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сидячий (офис, мало движения)",
                    callback_data="activity_sedentary",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Лёгкая (1-2 тренировки/нед)",
                    callback_data="activity_light",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Умеренная (3-4 тренировки/нед)",
                    callback_data="activity_moderate",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Высокая (5-6 тренировок/нед)",
                    callback_data="activity_high",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Очень высокая (2 тренировки/день)",
                    callback_data="activity_very_high",
                )
            ],
        ]
    )


def get_goal_keyboard() -> InlineKeyboardMarkup:
    """Goal selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Рекомпозиция", callback_data="goal_recomp"),
            ],
            [
                InlineKeyboardButton(text="Сушка", callback_data="goal_cut"),
            ],
            [
                InlineKeyboardButton(text="Набор массы", callback_data="goal_bulk"),
            ],
        ]
    )


def get_goal_speed_keyboard() -> InlineKeyboardMarkup:
    """Goal speed selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Бережно", callback_data="speed_gentle"),
                InlineKeyboardButton(text="Стандарт", callback_data="speed_standard"),
                InlineKeyboardButton(text="Агрессивно", callback_data="speed_aggressive"),
            ],
        ]
    )


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
                InlineKeyboardButton(text="🔄 Заново", callback_data="restart"),
            ],
        ]
    )


def get_exercises_keyboard(exercises: list[str]) -> InlineKeyboardMarkup:
    """Keyboard with user's recent exercises."""
    buttons = [
        [InlineKeyboardButton(text=ex, callback_data=f"exercise_{ex}")]
        for ex in exercises[:5]
    ]
    buttons.append(
        [InlineKeyboardButton(text="➕ Другое", callback_data="exercise_other")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_alert_keyboard(alert_type: str) -> InlineKeyboardMarkup:
    """Alert response keyboard."""
    if alert_type == "rapid_weight_loss":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Понял", callback_data="alert_ack"),
                    InlineKeyboardButton(
                        text="Скорректировать план", callback_data="alert_adjust"
                    ),
                ],
            ]
        )
    elif alert_type == "low_calories":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Напомни мой план", callback_data="alert_show_plan"
                    ),
                ],
            ]
        )
    elif alert_type == "missed_workouts":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Записать тренировку сейчас",
                        callback_data="alert_log_workout",
                    ),
                ],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Понял", callback_data="alert_ack")],
        ]
    )


def get_reminder_keyboard(reminder_type: str) -> InlineKeyboardMarkup:
    """Reminder response keyboard."""
    if reminder_type == "weigh":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Записать вес", callback_data="log_weight")],
            ]
        )
    elif reminder_type == "daily":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Калории", callback_data="log_calories"),
                    InlineKeyboardButton(text="Вода", callback_data="log_water"),
                ],
                [
                    InlineKeyboardButton(text="Сон", callback_data="log_sleep"),
                    InlineKeyboardButton(text="Всё записал ✓", callback_data="log_done"),
                ],
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=[])
