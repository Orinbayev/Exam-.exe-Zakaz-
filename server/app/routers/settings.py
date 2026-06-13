"""
Tizim sozlamalari va Excel eksport endpointlari.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
from ..database import get_db
from ..models import SystemSettings, ExamSession
from ..schemas import SettingUpdate
from ..auth import require_superadmin, require_teacher_or_admin
from ..models import User

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    settings = db.query(SystemSettings).all()
    return {s.key: s.value for s in settings}


@router.post("/")
def update_setting(
    data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    setting = db.query(SystemSettings).filter(SystemSettings.key == data.key).first()
    if setting:
        setting.value = data.value
    else:
        setting = SystemSettings(key=data.key, value=data.value)
        db.add(setting)
    db.commit()
    return {"message": "Sozlama saqlandi", "key": data.key}


@router.post("/telegram")
def save_telegram_settings(
    bot_token: str,
    notify_teacher: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    for key, value in [
        ("telegram_bot_token", bot_token),
        ("telegram_notify_teacher", str(notify_teacher)),
    ]:
        s = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if s:
            s.value = value
        else:
            db.add(SystemSettings(key=key, value=value))
    db.commit()
    return {"message": "Telegram sozlamalari saqlandi"}


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Natijalarni Excel faylga eksport qilish."""
    from ..excel_export import generate_results_excel

    q = db.query(ExamSession).filter(ExamSession.is_completed == True)
    if current_user.role != "superadmin":
        test_ids = [t.id for t in current_user.tests]
        q = q.filter(ExamSession.test_id.in_(test_ids))

    sessions = q.order_by(ExamSession.end_time.desc()).all()
    excel_bytes = generate_results_excel(sessions)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=natijalar.xlsx"}
    )
