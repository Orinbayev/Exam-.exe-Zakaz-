"""
Bot yordamchi funksiyalari.
"""
import json
from datetime import datetime
from ..database import SessionLocal
from ..models import SystemSettings, BotUser


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_bot_admins() -> list[str]:
    db = SessionLocal()
    try:
        s = db.query(SystemSettings).filter(SystemSettings.key == "bot_admin_ids").first()
        if s and s.value:
            return json.loads(s.value)
        return []
    finally:
        db.close()


def is_bot_admin(telegram_id: str) -> bool:
    return str(telegram_id) in get_bot_admins()


def get_or_create_bot_user(telegram_id: str, default_lang: str = "ru") -> dict:
    db = SessionLocal()
    try:
        u = db.query(BotUser).filter(BotUser.telegram_id == str(telegram_id)).first()
        if not u:
            u = BotUser(telegram_id=str(telegram_id), lang=default_lang)
            db.add(u)
            db.commit()
            db.refresh(u)
        else:
            u.last_seen = datetime.utcnow()
            db.commit()
        lang = u.lang
        role = u.role
        uid = u.id
        return {"lang": lang, "role": role, "id": uid}
    finally:
        db.close()


def set_user_lang(telegram_id: str, lang: str):
    db = SessionLocal()
    try:
        u = db.query(BotUser).filter(BotUser.telegram_id == str(telegram_id)).first()
        if u:
            u.lang = lang
            db.commit()
    finally:
        db.close()


def add_bot_admin(telegram_id: str) -> bool:
    """Admin qo'shish. True — muvaffaqiyatli, False — allaqachon bor."""
    db = SessionLocal()
    try:
        s = db.query(SystemSettings).filter(SystemSettings.key == "bot_admin_ids").first()
        admins = json.loads(s.value) if s and s.value else []
        if str(telegram_id) in admins:
            return False
        admins.append(str(telegram_id))
        if s:
            s.value = json.dumps(admins)
        else:
            db.add(SystemSettings(key="bot_admin_ids", value=json.dumps(admins)))
        db.commit()
        return True
    finally:
        db.close()


def remove_bot_admin(telegram_id: str) -> bool:
    """Admin o'chirish. True — o'chirildi, False — topilmadi."""
    db = SessionLocal()
    try:
        s = db.query(SystemSettings).filter(SystemSettings.key == "bot_admin_ids").first()
        admins = json.loads(s.value) if s and s.value else []
        if str(telegram_id) not in admins:
            return False
        admins.remove(str(telegram_id))
        s.value = json.dumps(admins)
        db.commit()
        return True
    finally:
        db.close()
