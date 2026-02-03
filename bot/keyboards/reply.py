from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Итоги сегодня"),
            ],
            [
                KeyboardButton(text="📝 Записать"),
                KeyboardButton(text="🏋️ Тренировка"),
            ],
            [
                KeyboardButton(text="📋 Мой план"),
                KeyboardButton(text="📈 Отчёты"),
            ],
            [
                KeyboardButton(text="💪 Силовой журнал"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
    )


def get_logging_keyboard() -> ReplyKeyboardMarkup:
    """Logging menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⚖️ Вес"),
                KeyboardButton(text="🍽 Калории"),
            ],
            [
                KeyboardButton(text="💧 Вода"),
                KeyboardButton(text="😴 Сон"),
            ],
            [
                KeyboardButton(text="◀️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_workout_type_keyboard() -> ReplyKeyboardMarkup:
    """Workout type selection keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏋️ Зал"),
                KeyboardButton(text="🏃 Кардио"),
            ],
            [
                KeyboardButton(text="🚶 Ходьба"),
                KeyboardButton(text="🎯 Другое"),
            ],
            [
                KeyboardButton(text="◀️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_strength_keyboard() -> ReplyKeyboardMarkup:
    """Strength journal keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить запись"),
            ],
            [
                KeyboardButton(text="📈 Прогресс по упражнению"),
            ],
            [
                KeyboardButton(text="◀️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_reports_keyboard() -> ReplyKeyboardMarkup:
    """Reports menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📈 График веса"),
                KeyboardButton(text="📊 Недельный отчёт"),
            ],
            [
                KeyboardButton(text="📅 Месячная сводка"),
                KeyboardButton(text="🔥 Streak"),
            ],
            [
                KeyboardButton(text="◀️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_settings_keyboard() -> ReplyKeyboardMarkup:
    """Settings menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Обновить профиль"),
            ],
            [
                KeyboardButton(text="⏰ Время напоминаний"),
            ],
            [
                KeyboardButton(text="🤖 AI-коуч: вкл/выкл"),
            ],
            [
                KeyboardButton(text="◀️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Simple back button keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel button keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )
