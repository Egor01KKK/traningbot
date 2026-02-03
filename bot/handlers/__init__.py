from typing import List
from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.menu import router as menu_router
from bot.handlers.logging import router as logging_router
from bot.handlers.workout import router as workout_router
from bot.handlers.strength import router as strength_router
from bot.handlers.reports import router as reports_router
from bot.handlers.settings import router as settings_router


def get_all_routers() -> List[Router]:
    """Get all handler routers."""
    return [
        start_router,
        menu_router,
        logging_router,
        workout_router,
        strength_router,
        reports_router,
        settings_router,
    ]
