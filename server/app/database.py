"""
Ma'lumotlar bazasi ulanishi.
- Local / Mac: SQLite (exam_system.db)
- Railway (cloud): PostgreSQL (DATABASE_URL env orqali avtomatik)
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
import os

import logging
_db_logger = logging.getLogger("exam_server.db")

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    # Railway / cloud PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"},
    )
    _is_sqlite = False
    _db_logger.warning("✅ DATABASE: PostgreSQL ishlatilmoqda (Railway)")
else:
    # Local SQLite
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "exam_system.db")
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    _is_sqlite = True
    _db_logger.warning("⚠️  DATABASE: SQLite ishlatilmoqda — DATABASE_URL o'rnatilmagan!")

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
