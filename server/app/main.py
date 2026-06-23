"""
FastAPI asosiy ilovasi - Smart Exam System Server.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .database import engine, Base, SessionLocal
from .models import User, SystemSettings
from .auth import hash_password
from .routers import auth_router, users, questions, tests, sessions, stats, settings as settings_router
from .routers import students as students_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exam_server")

app = FastAPI(
    title="Smart Exam System API",
    description="Maktab va o'quv markazlari uchun test tizimi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlarni ulash
app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(questions.router)
app.include_router(tests.router)
app.include_router(sessions.router)
app.include_router(stats.router)
app.include_router(settings_router.router)
app.include_router(students_router.router)


# ── Telegram webhook endpoint ─────────────────────────────────────────────────

@app.post("/bot/webhook")
async def telegram_webhook(request: Request):
    """Telegram Updates ni qabul qiladi — polling o'rniga."""
    from aiogram.types import Update
    from .bot.setup import get_bot, get_dp
    bot = get_bot()
    dp  = get_dp()
    if not bot or not dp:
        return JSONResponse({"ok": False, "error": "bot not ready"}, status_code=503)
    try:
        data   = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook update xatosi: {e}")
        return JSONResponse({"ok": False}, status_code=200)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Xato: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Serverda ichki xato yuz berdi"})


@app.on_event("startup")
async def startup():
    """Server ishga tushganda DB yaratish va super admin tekshirish."""
    import time
    from sqlalchemy import text

    for attempt in range(6):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Ma'lumotlar bazasi tayyor")
            break
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"DB ulanish xatosi ({attempt+1}/6): {e} — {wait}s kutilmoqda")
            if attempt == 5:
                logger.error("DB ga ulanib bo'lmadi, server davom etmoqda...")
                return
            time.sleep(wait)

    # Migrations: PostgreSQL DO-block — kolumn mavjud bo'lsa ham xato bermaydi
    try:
        with engine.connect() as conn:
            migrations = [
                # DO $$ ... $$ — kolumn mavjud bo'lsa EXCEPTION ni jimgina yutib yuboradi
                """DO $$ BEGIN ALTER TABLE student_classes ADD COLUMN is_active BOOLEAN DEFAULT FALSE;
                   EXCEPTION WHEN duplicate_column THEN NULL; END $$""",
                """DO $$ BEGIN ALTER TABLE questions ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                   EXCEPTION WHEN duplicate_column THEN NULL; END $$""",
                """DO $$ BEGIN ALTER TABLE categories ADD COLUMN time_limit INTEGER DEFAULT 30;
                   EXCEPTION WHEN duplicate_column THEN NULL; END $$""",
                """DO $$ BEGIN ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                   EXCEPTION WHEN duplicate_column THEN NULL; END $$""",
                # bot_users jadvali
                """CREATE TABLE IF NOT EXISTS bot_users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    lang VARCHAR(2) DEFAULT 'ru',
                    role VARCHAR(20) DEFAULT 'parent',
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""",
            ]
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"Migration OK: {sql[:80].strip()}")
                except Exception as mig_err:
                    logger.warning(f"Migration FAILED: {mig_err}")
    except Exception as e:
        logger.warning(f"Migration xatosi (e'tiborsiz): {e}")

    # Telegram bot — webhook orqali (polling emas)
    try:
        import os
        db_s = SessionLocal()
        try:
            tok_row = db_s.query(SystemSettings).filter(
                SystemSettings.key == "telegram_bot_token"
            ).first()
            token = tok_row.value if tok_row else None
        finally:
            db_s.close()

        if token:
            server_url = os.environ.get(
                "SERVER_URL", "https://exam-server-vq86.onrender.com"
            )
            webhook_url = f"{server_url}/bot/webhook"
            from .bot.setup import init_bot_dp, get_bot
            init_bot_dp(token)
            bot_tmp = get_bot()
            await bot_tmp.set_webhook(
                webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"],
            )
            logger.info(f"Bot webhook o'rnatildi: {webhook_url}")
        else:
            logger.warning("Bot token yo'q — webhook o'rnatilmadi")
    except Exception as e:
        logger.warning(f"Bot webhook xatosi (e'tiborsiz): {e}")

    try:
        db = SessionLocal()
        try:
            superadmin = db.query(User).filter(User.role == "superadmin").first()
            if not superadmin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    full_name="Super Administrator",
                    role="superadmin",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                logger.info("✅ Default Super Admin yaratildi: admin / admin123")

            defaults = {
                "telegram_notify_teacher": "true",
                "system_name": "Smart Exam System",
                "bot_admin_secret": "admin2024",
            }
            for key, value in defaults.items():
                if not db.query(SystemSettings).filter(SystemSettings.key == key).first():
                    db.add(SystemSettings(key=key, value=value))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Admin yaratishda xato (e'tiborsiz): {e}")

    logger.info("🚀 Smart Exam Server ishga tushdi!")


@app.get("/")
def root():
    return {
        "status": "online",
        "name": "Smart Exam System",
        "version": "1.0.0",
        "message": "Server ishlayapti! /docs sahifasida API hujjatlarini ko'ring."
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    from sqlalchemy import text
    from .database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}
