"""
Bot va Dispatcher global instansiyalari — webhook uchun.
"""
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

logger = logging.getLogger("exam_bot")

_bot: Bot | None = None
_dp:  Dispatcher | None = None


def get_bot() -> Bot | None:
    return _bot


def get_dp() -> Dispatcher | None:
    return _dp


def init_bot_dp(token: str):
    global _bot, _dp
    from .router_start     import router as start_router
    from .router_parent    import router as parent_router
    from .router_admin     import router as admin_router
    from .router_broadcast import router as broadcast_router

    _bot = Bot(token=token)
    _dp  = Dispatcher(storage=MemoryStorage())
    _dp.include_router(start_router)
    _dp.include_router(parent_router)
    _dp.include_router(admin_router)
    _dp.include_router(broadcast_router)
    logger.info("Bot va Dispatcher tayyor")
