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

    # Migrations: add missing columns safely
    try:
        with engine.connect() as conn:
            migrations = [
                "ALTER TABLE student_classes ADD COLUMN is_active BOOLEAN DEFAULT 0",
                "ALTER TABLE questions ADD COLUMN is_active BOOLEAN DEFAULT 1",
                "ALTER TABLE categories ADD COLUMN time_limit INTEGER DEFAULT 30",
                "ALTER TABLE categories ADD COLUMN is_active BOOLEAN DEFAULT 1",
            ]
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Migration xatosi (e'tiborsiz): {e}")

    # Telegram bot background ishga tushirish
    try:
        import asyncio
        from .bot.runner import start_bot_background
        asyncio.create_task(start_bot_background())
        logger.info("Telegram bot vazifasi boshlandi")
    except Exception as e:
        logger.warning(f"Bot ishga tushishda xato (e'tiborsiz): {e}")

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
