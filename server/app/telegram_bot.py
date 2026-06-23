"""
Telegram bot integratsiyasi.
- O'qituvchiga natija yuborish
- Ota-onaga farzand natijalari yuborish
"""
import asyncio
from typing import Optional


async def get_setting(db, key: str) -> Optional[str]:
    from .models import SystemSettings
    s = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return s.value if s else None


async def send_message(token: str, chat_id: str, text: str) -> bool:
    """Telegram API orqali xabar yuborish."""
    try:
        import httpx
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            result = resp.json()
            return result.get("ok", False)
    except Exception as e:
        print(f"Telegram xato: {e}")
        return False


def _grade_emoji(grade: str) -> str:
    return {"5": "🏆", "4": "⭐", "3": "✅", "2": "📚"}.get(grade, "📋")


def _grade_text(grade: str) -> str:
    return {
        "5": "A'LO (5)",
        "4": "YAXSHI (4)",
        "3": "QONIQARLI (3)",
        "2": "QONIQARSIZ (2)"
    }.get(grade, grade)


async def notify_result(session, db):
    """Exam natijasini o'qituvchi va ota-onaga yuborish."""
    token = await get_setting(db, "telegram_bot_token")
    if not token:
        return

    test = session.test
    teacher = test.teacher if test else None
    grade_emoji = _grade_emoji(session.grade or "")
    grade_text = _grade_text(session.grade or "")
    result_emoji = "✅" if session.is_passed else "❌"

    # ── O'qituvchiga xabar ────────────────────────────────────────────────────
    notify_teacher = await get_setting(db, "telegram_notify_teacher")
    if notify_teacher and notify_teacher.lower() == "true":
        if teacher and teacher.telegram_chat_id:
            teacher_msg = (
                f"{result_emoji} <b>Yangi natija!</b>\n\n"
                f"👤 O'quvchi: <b>{session.student_name} {session.student_lastname}</b>\n"
                f"🏫 Sinf: {session.student_class}\n"
                f"📝 Test: <b>{test.name if test else '—'}</b>\n"
                f"📊 Ball: <b>{session.score_percent:.1f}%</b>\n"
                f"{grade_emoji} Baho: <b>{grade_text}</b>\n"
                f"✔️ To'g'ri: {session.correct_count}/{session.total_questions}\n"
                f"{'🎉 Testdan o\'tdi!' if session.is_passed else '⚠️ Testdan o\'tmadi'}"
            )
            await send_message(token, teacher.telegram_chat_id, teacher_msg)

    # ── Ota-onaga xabar ───────────────────────────────────────────────────────
    # student_class nomidan DB dan Student topamiz
    try:
        from .models import Student, StudentClass
        # Sinf nomiga mos sinf topish
        cls = db.query(StudentClass).filter(
            StudentClass.name == session.student_class
        ).first()
        if cls:
            # Ism-familyaga mos o'quvchi
            student = db.query(Student).filter(
                Student.class_id == cls.id,
                Student.first_name == session.student_name,
                Student.last_name == session.student_lastname
            ).first()
            if student and student.parent_telegram_id:
                parent_msg = (
                    f"{grade_emoji} <b>Hurmatli ota-ona!</b>\n\n"
                    f"Farzandingiz <b>{session.student_name} {session.student_lastname}</b>\n"
                    f"«{test.name if test else '—'}» testini topshirdi.\n\n"
                    f"📊 <b>Natija: {session.score_percent:.1f}%</b>\n"
                    f"{grade_emoji} <b>Baho: {grade_text}</b>\n"
                    f"✔️ To'g'ri javoblar: {session.correct_count}/{session.total_questions}\n\n"
                    f"{'🎉 Tabriklaymiz! Farzandingiz testdan muvaffaqiyatli o\'tdi!' if session.is_passed else '⚠️ Farzandingiz testdan o\'ta olmadi. Ko\'proq o\'qish kerak.'}"
                )
                await send_message(token, student.parent_telegram_id, parent_msg)
    except Exception as e:
        print(f"Ota-onaga xabar yuborishda xato: {e}")


async def test_bot_token(token: str, chat_id: str) -> bool:
    result = await send_message(
        token, chat_id,
        "✅ <b>Smart Exam System</b>\nBot muvaffaqiyatli ulandi! 🎓"
    )
    return result
