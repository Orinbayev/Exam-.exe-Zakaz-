"""
Bot ishga tushirish — background task sifatida.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .router_start import router as start_router
from .router_parent import router as parent_router
from .router_admin import router as admin_router
from .router_broadcast import router as broadcast_router

logger = logging.getLogger("exam_bot")


async def run_bot(token: str):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(parent_router)
    dp.include_router(admin_router)
    dp.include_router(broadcast_router)

    logger.info("Bot ishga tushdi!")
    try:
        # drop_pending_updates=True — qayta ishga tushganda eski xabarlarni o'tkazib yuboradi
        # va oldingi polling sessiyasini to'xtatadi (Conflict xatosini oldini oladi)
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    except Exception as e:
        logger.error(f"Bot xatosi: {e}")
    finally:
        await bot.session.close()


async def start_bot_background():
    from ..database import SessionLocal
    from ..models import SystemSettings

    db = SessionLocal()
    try:
        s = db.query(SystemSettings).filter(SystemSettings.key == "telegram_bot_token").first()
        token = s.value if s else None
    finally:
        db.close()

    if not token:
        logger.warning("Bot token yo'q — bot ishga tushmadi. Sozlamalardan token kiriting.")
        return

    await run_bot(token)
