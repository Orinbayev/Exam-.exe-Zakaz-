"""
Ota-ona paneli — farzandlar va natijalar.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from .texts import T
from .keyboards import children_kb, back_children_kb, parent_main_kb, lang_change_kb
from .helpers import get_or_create_bot_user
from ..database import SessionLocal
from ..models import Student, ExamSession

router = Router()


def get_parent_children(telegram_id: str) -> list:
    db = SessionLocal()
    try:
        students = db.query(Student).filter(
            Student.parent_telegram_id == str(telegram_id)
        ).all()
        return [
            {
                "id": s.id,
                "first": s.first_name,
                "last": s.last_name,
                "cls": s.student_class.name if s.student_class else "?",
            }
            for s in students
        ]
    finally:
        db.close()


def get_student_results(student_first: str, student_last: str, student_cls: str, limit: int = 15):
    db = SessionLocal()
    try:
        sessions = (
            db.query(ExamSession)
            .filter(
                ExamSession.student_name == student_first,
                ExamSession.student_lastname == student_last,
                ExamSession.student_class == student_cls,
                ExamSession.is_completed == True,
            )
            .order_by(ExamSession.end_time.desc())
            .limit(limit)
            .all()
        )
        # session yopilishidan oldin lazy munosabatlarni yuklab olamiz
        result = []
        for ses in sessions:
            result.append({
                "test_name": ses.test.name if ses.test else "?",
                "score": ses.score_percent,
                "grade": ses.grade or "?",
                "is_passed": ses.is_passed,
                "end_time": ses.end_time,
            })
        return result
    finally:
        db.close()


@router.callback_query(F.data == "parent_children")
async def show_children(call: CallbackQuery):
    tid = str(call.from_user.id)
    user = get_or_create_bot_user(tid)
    lang = user["lang"]
    children = get_parent_children(tid)
    if not children:
        await call.message.edit_text(
            T(lang, "no_children", chat_id=tid), parse_mode="HTML"
        )
        await call.answer()
        return
    await call.message.edit_text(
        T(lang, "children_list"),
        reply_markup=children_kb(lang, children),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("child:"))
async def show_child_results(call: CallbackQuery):
    student_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    user = get_or_create_bot_user(tid)
    lang = user["lang"]

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == student_id).first()
        if not s:
            await call.answer("Not found")
            return
        cls_name = s.student_class.name if s.student_class else "?"
        first_name = s.first_name
        last_name = s.last_name
    finally:
        db.close()

    sessions = get_student_results(first_name, last_name, cls_name)
    text = T(lang, "child_results_title", name=first_name, last=last_name, cls=cls_name)
    if not sessions:
        text += T(lang, "no_results")
    else:
        for ses in sessions:
            date = ses["end_time"].strftime("%d.%m.%Y %H:%M") if ses["end_time"] else "?"
            status = T(lang, "passed") if ses["is_passed"] else T(lang, "failed")
            text += T(
                lang,
                "result_row",
                test=ses["test_name"],
                score=ses["score"],
                grade=ses["grade"],
                status=status,
                date=date,
            )

    await call.message.edit_text(
        text, reply_markup=back_children_kb(lang), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "parent_settings")
async def parent_settings(call: CallbackQuery):
    tid = str(call.from_user.id)
    user = get_or_create_bot_user(tid)
    lang = user["lang"]
    await call.message.edit_text(
        T(lang, "lang_btn"),
        reply_markup=lang_change_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "parent_main")
async def parent_main(call: CallbackQuery):
    tid = str(call.from_user.id)
    user = get_or_create_bot_user(tid)
    lang = user["lang"]
    name = call.from_user.first_name or ""
    await call.message.edit_text(
        T(lang, "start_welcome_parent", name=name),
        reply_markup=parent_main_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()
