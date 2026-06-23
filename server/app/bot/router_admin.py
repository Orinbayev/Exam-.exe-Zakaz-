"""
Admin paneli — statistika, o'quvchilar, savollar, top, fanlar, adminlar.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .states import QuestionAdd
from .texts import T
from .keyboards import (
    admin_main_kb, back_admin_kb, subjects_kb,
    correct_kb, difficulty_kb, confirm_kb, classes_kb,
    admin_questions_kb,
)
from .helpers import get_or_create_bot_user, is_bot_admin
from ..database import SessionLocal
from ..models import (
    Category, Question, ExamSession, Student, StudentClass,
    BotUser, User,
)

router = Router()


def _check_admin(tid: str) -> bool:
    return is_bot_admin(tid)


def _lang(tid: str) -> str:
    user = get_or_create_bot_user(tid)
    return user["lang"]


# ── Admin menu ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_menu")
async def admin_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    await call.message.edit_text(
        T(lang, "admin_menu_title"),
        reply_markup=admin_main_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        from sqlalchemy import func
        total = db.query(ExamSession).filter(ExamSession.is_completed == True).count()
        passed = db.query(ExamSession).filter(
            ExamSession.is_completed == True, ExamSession.is_passed == True
        ).count()
        failed = total - passed
        avg_row = (
            db.query(func.avg(ExamSession.score_percent))
            .filter(ExamSession.is_completed == True)
            .scalar()
        )
        avg = avg_row or 0.0
        students_n = db.query(Student).count()
        classes_n = db.query(StudentClass).count()
        questions_n = db.query(Question).filter(Question.is_active == True).count()
    finally:
        db.close()

    text = (
        T(lang, "stats_title")
        + T(lang, "stats_total_exams", n=total)
        + T(lang, "stats_passed", n=passed)
        + T(lang, "stats_failed", n=failed)
        + T(lang, "stats_avg", v=avg)
        + T(lang, "stats_students", n=students_n)
        + T(lang, "stats_classes", n=classes_n)
        + T(lang, "stats_questions", n=questions_n)
    )
    await call.message.edit_text(
        text, reply_markup=back_admin_kb(lang), parse_mode="HTML"
    )
    await call.answer()


# ── Top students ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_top")
async def admin_top(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        rows = (
            db.query(ExamSession)
            .filter(ExamSession.is_completed == True)
            .order_by(ExamSession.score_percent.desc())
            .limit(10)
            .all()
        )
        # session yopilishidan oldin lazy munosabatlarni yuklab olamiz
        top = [
            {
                "last": s.student_lastname,
                "first": s.student_name,
                "cls": s.student_class,
                "score": s.score_percent,
                "test": s.test.name[:20] if s.test else "?",
            }
            for s in rows
        ]
    finally:
        db.close()

    text = T(lang, "top_title")
    if not top:
        text += T(lang, "no_top")
    else:
        for i, s in enumerate(top, 1):
            text += T(
                lang,
                "top_row",
                rank=i,
                last=s["last"],
                first=s["first"],
                cls=s["cls"],
                score=s["score"],
                test=s["test"],
            )

    await call.message.edit_text(
        text, reply_markup=back_admin_kb(lang), parse_mode="HTML"
    )
    await call.answer()


# ── Subjects ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_subjects")
async def admin_subjects(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        cats = db.query(Category).all()
        cat_list = []
        for c in cats:
            qcount = (
                db.query(Question)
                .filter(Question.category_id == c.id, Question.is_active == True)
                .count()
            )
            cat_list.append({"id": c.id, "name": c.name, "q": qcount})
    finally:
        db.close()

    if not cat_list:
        text = T(lang, "no_subjects")
    else:
        text = T(lang, "subjects_title", n=len(cat_list))
        for c in cat_list:
            text += T(lang, "subject_row", name=c["name"], q=c["q"])

    await call.message.edit_text(
        text, reply_markup=back_admin_kb(lang), parse_mode="HTML"
    )
    await call.answer()


# ── Students ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_students")
async def admin_students(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        classes = db.query(StudentClass).all()
        cls_list = []
        for c in classes:
            n = db.query(Student).filter(Student.class_id == c.id).count()
            cls_list.append({"id": c.id, "name": c.name, "n": n})
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "students_classes"),
        reply_markup=classes_kb(lang, cls_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("cls:"))
async def show_class_students(call: CallbackQuery):
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        if not cls:
            await call.answer("Not found")
            return
        students = db.query(Student).filter(Student.class_id == class_id).all()
        cls_name = cls.name
        student_rows = [
            {"first": s.first_name, "last": s.last_name} for s in students
        ]
    finally:
        db.close()

    text = T(lang, "students_of_class", cls=cls_name)
    if not student_rows:
        text += T(lang, "no_students_in_class")
    else:
        for i, s in enumerate(student_rows, 1):
            text += T(lang, "student_row", i=i, last=s["last"], first=s["first"]) + "\n"

    await call.message.edit_text(
        text, reply_markup=back_admin_kb(lang), parse_mode="HTML"
    )
    await call.answer()


# ── Questions / Add via FSM ────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_questions")
async def admin_questions(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        cats = db.query(Category).all()
        cat_list = [{"id": c.id, "name": c.name} for c in cats]
    finally:
        db.close()

    header = T(lang, "subjects_title", n=len(cat_list)) if cat_list else T(lang, "no_subjects")
    await call.message.edit_text(
        header,
        reply_markup=admin_questions_kb(lang, cat_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "q_add_start")
async def q_add_start(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        cats = db.query(Category).all()
        cat_list = [{"id": c.id, "name": c.name} for c in cats]
    finally:
        db.close()

    if not cat_list:
        await call.answer(T(lang, "no_subjects"), show_alert=True)
        return

    await state.set_state(QuestionAdd.subject)
    await call.message.edit_text(
        T(lang, "q_choose_subject"),
        reply_markup=subjects_kb(cat_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(QuestionAdd.subject, F.data.startswith("qsubj:"))
async def q_got_subject(call: CallbackQuery, state: FSMContext):
    # Format: qsubj:{id}:{name}
    parts = call.data.split(":", 2)
    subj_id = int(parts[1])
    subj_name = parts[2] if len(parts) > 2 else str(subj_id)
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(subject_id=subj_id, subject_name=subj_name)
    await state.set_state(QuestionAdd.text)
    await call.message.edit_text(T(lang, "q_ask_text"), parse_mode="HTML")
    await call.answer()


@router.message(QuestionAdd.text)
async def q_got_text(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(text=message.text)
    await state.set_state(QuestionAdd.opt_a)
    await message.answer(T(lang, "q_ask_a"), parse_mode="HTML")


@router.message(QuestionAdd.opt_a)
async def q_got_a(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(opt_a=message.text)
    await state.set_state(QuestionAdd.opt_b)
    await message.answer(T(lang, "q_ask_b"), parse_mode="HTML")


@router.message(QuestionAdd.opt_b)
async def q_got_b(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(opt_b=message.text)
    await state.set_state(QuestionAdd.opt_c)
    await message.answer(T(lang, "q_ask_c"), parse_mode="HTML")


@router.message(QuestionAdd.opt_c)
async def q_got_c(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(opt_c=message.text)
    await state.set_state(QuestionAdd.opt_d)
    await message.answer(T(lang, "q_ask_d"), parse_mode="HTML")


@router.message(QuestionAdd.opt_d)
async def q_got_d(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(opt_d=message.text)
    await state.set_state(QuestionAdd.correct)
    await message.answer(T(lang, "q_ask_correct"), reply_markup=correct_kb(), parse_mode="HTML")


@router.callback_query(QuestionAdd.correct, F.data.startswith("correct:"))
async def q_got_correct(call: CallbackQuery, state: FSMContext):
    correct = call.data.split(":")[1]
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(correct=correct)
    await state.set_state(QuestionAdd.difficulty)
    await call.message.edit_text(
        T(lang, "q_ask_diff"), reply_markup=difficulty_kb(lang), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(QuestionAdd.difficulty, F.data.startswith("diff:"))
async def q_got_diff(call: CallbackQuery, state: FSMContext):
    diff = call.data.split(":")[1]
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(difficulty=diff)
    data = await state.get_data()

    # diff key: easy→easy, medium→med, hard→hard
    diff_key_map = {"easy": "easy", "medium": "med", "hard": "hard"}
    diff_text = T(lang, f"q_diff_{diff_key_map.get(diff, diff[:3])}")
    text = T(
        lang,
        "q_confirm",
        text=data["text"],
        a=data["opt_a"],
        b=data["opt_b"],
        c=data["opt_c"],
        d=data["opt_d"],
        correct=data["correct"],
        diff=diff_text,
    )

    await state.set_state(QuestionAdd.confirm)
    await call.message.edit_text(text, reply_markup=confirm_kb(lang), parse_mode="HTML")
    await call.answer()


@router.callback_query(QuestionAdd.confirm, F.data == "q_confirm_yes")
async def q_save(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        teacher = db.query(User).filter(User.role.in_(["superadmin", "teacher"])).first()
        if not teacher:
            await call.answer("No teacher found", show_alert=True)
            return
        q = Question(
            text=data["text"],
            option_a=data["opt_a"],
            option_b=data["opt_b"],
            option_c=data["opt_c"],
            option_d=data["opt_d"],
            correct_answer=data["correct"],
            category_id=data["subject_id"],
            difficulty=data["difficulty"],
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        qid = q.id
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "q_saved", id=qid),
        reply_markup=back_admin_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.in_({"q_confirm_no", "q_cancel"}))
async def q_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await call.message.edit_text(
        T(lang, "q_cancel"), reply_markup=back_admin_kb(lang), parse_mode="HTML"
    )
    await call.answer()


# ── Admins list ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_admins")
async def admin_admins(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    from .helpers import get_bot_admins
    admins = get_bot_admins()
    if admins:
        admin_list = "".join(T(lang, "admin_row", tid=a) for a in admins)
    else:
        admin_list = T(lang, "no_admins")

    await call.message.edit_text(
        T(lang, "admins_title", list=admin_list),
        reply_markup=back_admin_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()
