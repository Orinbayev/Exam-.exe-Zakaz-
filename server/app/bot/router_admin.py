"""
Admin paneli — statistika, o'quvchilar, savollar, top, fanlar, adminlar.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .states import QuestionAdd, CategoryAdd, ClassAdd, StudentAdd, StudentEdit, ClassEdit, AdminAdd
from .texts import T
from .keyboards import (
    admin_main_kb, back_admin_kb, subjects_kb,
    correct_kb, difficulty_kb, confirm_kb,
    admin_questions_kb, admin_subjects_kb, admin_classes_kb,
    class_detail_kb, skip_kb,
    subjects_list_kb, fan_manage_kb, fan_del_confirm_kb,
    cls_manage_kb, cls_del_confirm_kb,
    students_list_kb, student_manage_kb, std_del_confirm_kb,
    admins_manage_kb, admin_add_confirm_kb, admin_del_confirm_kb,
)
from .helpers import get_or_create_bot_user, is_bot_admin, get_bot_admins, add_bot_admin, remove_bot_admin
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
            qcount = db.query(Question).filter(Question.category_id == c.id, Question.is_active == True).count()
            cat_list.append({"id": c.id, "name": c.name, "q": qcount, "is_active": bool(c.is_active)})
    finally:
        db.close()

    text = T(lang, "subjects_title", n=len(cat_list)) if cat_list else T(lang, "no_subjects")
    await call.message.edit_text(
        text, reply_markup=subjects_list_kb(lang, cat_list), parse_mode="HTML"
    )
    await call.answer()


# ── Fan detail / toggle / delete ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("fan:"))
async def fan_detail(call: CallbackQuery, state: FSMContext):
    await state.clear()
    fan_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        c = db.query(Category).filter(Category.id == fan_id).first()
        if not c:
            await call.answer("Not found")
            return
        qcount = db.query(Question).filter(Question.category_id == fan_id, Question.is_active == True).count()
        name, time_limit, is_active = c.name, c.time_limit or 30, bool(c.is_active)
    finally:
        db.close()

    status = T(lang, "active") if is_active else T(lang, "inactive")
    text = T(lang, "fan_detail", name=name, time=time_limit, q=qcount, status=status)
    await call.message.edit_text(text, reply_markup=fan_manage_kb(lang, fan_id, is_active, name), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("fan_addq:"))
async def fan_addq_start(call: CallbackQuery, state: FSMContext):
    """Fan sahifasidan to'g'ridan-to'g'ri savol qo'shish — fan tanlash bosqichini o'tkazib."""
    fan_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    db = SessionLocal()
    try:
        cat = db.query(Category).filter(Category.id == fan_id).first()
        fan_name = cat.name if cat else str(fan_id)
    finally:
        db.close()
    await state.update_data(subject_id=fan_id, subject_name=fan_name)
    await state.set_state(QuestionAdd.text)
    await call.message.edit_text(
        T(lang, "q_ask_text") + f"\n\n📚 <b>{fan_name}</b>",
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("fan_toggle:"))
async def fan_toggle(call: CallbackQuery):
    fan_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        c = db.query(Category).filter(Category.id == fan_id).first()
        if not c:
            await call.answer("Not found")
            return
        c.is_active = not bool(c.is_active)
        db.commit()
        name, is_active = c.name, bool(c.is_active)
        qcount = db.query(Question).filter(Question.category_id == fan_id, Question.is_active == True).count()
        time_limit = c.time_limit or 30
    finally:
        db.close()

    key = "fan_toggled_on" if is_active else "fan_toggled_off"
    status = T(lang, "active") if is_active else T(lang, "inactive")
    text = T(lang, "fan_detail", name=name, time=time_limit, q=qcount, status=status)
    await call.message.edit_text(text, reply_markup=fan_manage_kb(lang, fan_id, is_active, name), parse_mode="HTML")
    await call.answer(T(lang, key, name=name), show_alert=False)


@router.callback_query(F.data.startswith("fan_del_ask:"))
async def fan_del_ask(call: CallbackQuery):
    fan_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        c = db.query(Category).filter(Category.id == fan_id).first()
        name = c.name if c else "?"
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "fan_del_ask", name=name),
        reply_markup=fan_del_confirm_kb(lang, fan_id),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("fan_del_ok:"))
async def fan_del_ok(call: CallbackQuery):
    fan_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        c = db.query(Category).filter(Category.id == fan_id).first()
        if not c:
            await call.answer("Not found")
            return
        name = c.name
        db.delete(c)
        db.commit()
        cats = db.query(Category).all()
        cat_list = []
        for cat in cats:
            qcount = db.query(Question).filter(Question.category_id == cat.id, Question.is_active == True).count()
            cat_list.append({"id": cat.id, "name": cat.name, "q": qcount, "is_active": bool(cat.is_active)})
    finally:
        db.close()

    text = T(lang, "fan_deleted", name=name)
    await call.message.edit_text(text, reply_markup=subjects_list_kb(lang, cat_list), parse_mode="HTML")
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
        reply_markup=admin_classes_kb(lang, cls_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("cls:"))
async def class_detail(call: CallbackQuery, state: FSMContext):
    await state.clear()
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        if not cls:
            await call.answer("Not found")
            return
        n = db.query(Student).filter(Student.class_id == class_id).count()
        cls_name, is_active = cls.name, bool(cls.is_active)
    finally:
        db.close()

    status = T(lang, "active") if is_active else T(lang, "inactive")
    text = T(lang, "cls_detail", name=cls_name, n=n, status=status)
    await call.message.edit_text(text, reply_markup=cls_manage_kb(lang, class_id, is_active), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("cls_toggle:"))
async def cls_toggle(call: CallbackQuery):
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        if not cls:
            await call.answer("Not found")
            return
        cls.is_active = not bool(cls.is_active)
        db.commit()
        n = db.query(Student).filter(Student.class_id == class_id).count()
        cls_name, is_active = cls.name, bool(cls.is_active)
    finally:
        db.close()

    key = "cls_toggled_on" if is_active else "cls_toggled_off"
    status = T(lang, "active") if is_active else T(lang, "inactive")
    text = T(lang, "cls_detail", name=cls_name, n=n, status=status)
    await call.message.edit_text(text, reply_markup=cls_manage_kb(lang, class_id, is_active), parse_mode="HTML")
    await call.answer(T(lang, key, name=cls_name), show_alert=False)


@router.callback_query(F.data.startswith("cls_edit:"))
async def cls_edit_start(call: CallbackQuery, state: FSMContext):
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        name = cls.name if cls else "?"
    finally:
        db.close()
    await state.update_data(class_id=class_id)
    await state.set_state(ClassEdit.new_name)
    await call.message.edit_text(
        T(lang, "cls_edit_ask", name=name),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(ClassEdit.new_name)
async def cls_edit_save(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    new_name = message.text.strip() if message.text else ""
    if not new_name:
        await message.answer("❗ Nom bo'sh bo'lishi mumkin emas.")
        return
    data = await state.get_data()
    class_id = data["class_id"]
    await state.clear()
    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        if not cls:
            await message.answer("Sinf topilmadi.")
            return
        cls.name = new_name
        db.commit()
        is_active = bool(cls.is_active)
    finally:
        db.close()
    await message.answer(
        T(lang, "cls_edited", name=new_name),
        reply_markup=cls_manage_kb(lang, class_id, is_active),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("cls_del_ask:"))
async def cls_del_ask(call: CallbackQuery):
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        name = cls.name if cls else "?"
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "cls_del_ask", name=name),
        reply_markup=cls_del_confirm_kb(lang, class_id),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("cls_del_ok:"))
async def cls_del_ok(call: CallbackQuery):
    class_id = int(call.data.split(":")[1])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        if not cls:
            await call.answer("Not found")
            return
        name = cls.name
        db.query(Student).filter(Student.class_id == class_id).delete()
        db.delete(cls)
        db.commit()
        classes = db.query(StudentClass).all()
        cls_list = []
        for c in classes:
            n = db.query(Student).filter(Student.class_id == c.id).count()
            cls_list.append({"id": c.id, "name": c.name, "n": n})
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "cls_deleted", name=name),
        reply_markup=admin_classes_kb(lang, cls_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("cls_students:"))
async def cls_students(call: CallbackQuery, state: FSMContext):
    await state.clear()
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
        std_list = [{"id": s.id, "first": s.first_name, "last": s.last_name} for s in students]
    finally:
        db.close()

    text = T(lang, "students_of_class", cls=cls_name)
    if not std_list:
        text += T(lang, "no_students_in_class")
    await call.message.edit_text(
        text, reply_markup=students_list_kb(lang, std_list, class_id), parse_mode="HTML"
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


# ── Fan yaratish (CategoryAdd FSM) ────────────────────────────────────────────

@router.callback_query(F.data == "fan_add_start")
async def fan_add_start(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    await state.set_state(CategoryAdd.name)
    await call.message.edit_text(T(lang, "fan_add_ask_name"), parse_mode="HTML")
    await call.answer()


@router.message(CategoryAdd.name)
async def fan_got_name(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(name=message.text.strip())
    await state.set_state(CategoryAdd.time_limit)
    await message.answer(T(lang, "fan_add_ask_time"), parse_mode="HTML")


@router.message(CategoryAdd.time_limit)
async def fan_got_time(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer(T(lang, "fan_add_time_invalid"), parse_mode="HTML")
        return  # holatni o'zgartirmaymiz, qayta so'raymiz
    await state.update_data(time_limit=int(text))
    data = await state.get_data()
    await state.set_state(CategoryAdd.confirm)
    await message.answer(
        T(lang, "fan_add_confirm", name=data["name"], time=data["time_limit"]),
        reply_markup=confirm_kb(lang, yes_cb="fan_confirm_yes", no_cb="fan_confirm_no"),
        parse_mode="HTML",
    )


@router.callback_query(CategoryAdd.confirm, F.data == "fan_confirm_yes")
async def fan_save(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        teacher = db.query(User).filter(User.role == "superadmin").first()
        if not teacher:
            teacher = db.query(User).first()
        cat = Category(
            name=data["name"],
            teacher_id=teacher.id,
            time_limit=data["time_limit"],
        )
        db.add(cat)
        db.commit()
        saved_name = data["name"]
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "fan_add_saved", name=saved_name),
        reply_markup=admin_subjects_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "fan_confirm_no")
async def fan_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await call.message.edit_text(
        T(lang, "fan_add_cancel"),
        reply_markup=admin_subjects_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


# ── Sinf qo'shish (ClassAdd FSM) ──────────────────────────────────────────────

@router.callback_query(F.data == "cls_add_start")
async def cls_add_start(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    await state.set_state(ClassAdd.name)
    await call.message.edit_text(T(lang, "cls_add_ask_name"), parse_mode="HTML")
    await call.answer()


@router.message(ClassAdd.name)
async def cls_got_name(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(name=message.text.strip())
    data = await state.get_data()
    await state.set_state(ClassAdd.confirm)
    await message.answer(
        T(lang, "cls_add_confirm", name=data["name"]),
        reply_markup=confirm_kb(lang, yes_cb="cls_confirm_yes", no_cb="cls_confirm_no"),
        parse_mode="HTML",
    )


@router.callback_query(ClassAdd.confirm, F.data == "cls_confirm_yes")
async def cls_save(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        teacher = db.query(User).filter(User.role == "superadmin").first()
        if not teacher:
            teacher = db.query(User).first()
        cls = StudentClass(
            name=data["name"],
            teacher_id=teacher.id,
            is_active=False,
        )
        db.add(cls)
        db.commit()
        saved_name = data["name"]
        cls_list = []
        for c in db.query(StudentClass).all():
            n = db.query(Student).filter(Student.class_id == c.id).count()
            cls_list.append({"id": c.id, "name": c.name, "n": n})
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "cls_add_saved", name=saved_name),
        reply_markup=admin_classes_kb(lang, cls_list),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "cls_confirm_no")
async def cls_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        cls_list = []
        for c in db.query(StudentClass).all():
            n = db.query(Student).filter(Student.class_id == c.id).count()
            cls_list.append({"id": c.id, "name": c.name, "n": n})
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "cls_add_cancel"),
        reply_markup=admin_classes_kb(lang, cls_list),
        parse_mode="HTML",
    )
    await call.answer()


# ── O'quvchi detail / tahrirlash / o'chirish ──────────────────────────────────

@router.callback_query(F.data.startswith("std:"))
async def std_detail(call: CallbackQuery, state: FSMContext):
    await state.clear()
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == student_id).first()
        if not s:
            await call.answer("Not found")
            return
        cls = db.query(StudentClass).filter(StudentClass.id == s.class_id).first()
        cls_name = cls.name if cls else "?"
        data = {
            "first": s.first_name, "last": s.last_name,
            "cls": cls_name, "parent": s.parent_telegram_id or "—",
        }
    finally:
        db.close()

    text = T(lang, "std_detail", **data)
    await call.message.edit_text(
        text, reply_markup=student_manage_kb(lang, student_id, class_id), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("std_del_ask:"))
async def std_del_ask(call: CallbackQuery):
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == student_id).first()
        first, last = (s.first_name, s.last_name) if s else ("?", "?")
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "std_del_ask", first=first, last=last),
        reply_markup=std_del_confirm_kb(lang, student_id, class_id),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("std_del_ok:"))
async def std_del_ok(call: CallbackQuery):
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == student_id).first()
        if not s:
            await call.answer("Not found")
            return
        first, last = s.first_name, s.last_name
        db.delete(s)
        db.commit()
        stds = db.query(Student).filter(Student.class_id == class_id).all()
        std_list = [{"id": x.id, "first": x.first_name, "last": x.last_name} for x in stds]
        cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
        cls_name = cls.name if cls else "?"
    finally:
        db.close()

    await call.message.edit_text(
        T(lang, "std_deleted", first=first, last=last),
        reply_markup=students_list_kb(lang, std_list, class_id),
        parse_mode="HTML",
    )
    await call.answer()


# ── O'quvchi tahrirlash (StudentEdit FSM) ─────────────────────────────────────

@router.callback_query(F.data.startswith("std_edit_f:"))
async def std_edit_fname_start(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(student_id=student_id, class_id=class_id)
    await state.set_state(StudentEdit.first_name)
    await call.message.edit_text(T(lang, "std_edit_ask_fname"), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("std_edit_l:"))
async def std_edit_lname_start(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(student_id=student_id, class_id=class_id)
    await state.set_state(StudentEdit.last_name)
    await call.message.edit_text(T(lang, "std_edit_ask_lname"), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("std_edit_p:"))
async def std_edit_parent_start(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    student_id, class_id = int(parts[1]), int(parts[2])
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.update_data(student_id=student_id, class_id=class_id)
    await state.set_state(StudentEdit.parent_tg)
    await call.message.edit_text(
        T(lang, "std_edit_ask_parent"),
        reply_markup=skip_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(StudentEdit.first_name)
async def std_save_fname(message: Message, state: FSMContext):
    data = await state.get_data()
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == data["student_id"]).first()
        if not s:
            await message.answer(T(lang, "error"))
            return
        s.first_name = message.text.strip()
        db.commit()
        first, last, class_id = s.first_name, s.last_name, s.class_id
        stds = db.query(Student).filter(Student.class_id == class_id).all()
        std_list = [{"id": x.id, "first": x.first_name, "last": x.last_name} for x in stds]
    finally:
        db.close()

    await message.answer(
        T(lang, "std_updated", first=first, last=last),
        reply_markup=students_list_kb(lang, std_list, data["class_id"]),
        parse_mode="HTML",
    )


@router.message(StudentEdit.last_name)
async def std_save_lname(message: Message, state: FSMContext):
    data = await state.get_data()
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == data["student_id"]).first()
        if not s:
            await message.answer(T(lang, "error"))
            return
        s.last_name = message.text.strip()
        db.commit()
        first, last, class_id = s.first_name, s.last_name, s.class_id
        stds = db.query(Student).filter(Student.class_id == class_id).all()
        std_list = [{"id": x.id, "first": x.first_name, "last": x.last_name} for x in stds]
    finally:
        db.close()

    await message.answer(
        T(lang, "std_updated", first=first, last=last),
        reply_markup=students_list_kb(lang, std_list, data["class_id"]),
        parse_mode="HTML",
    )


@router.message(StudentEdit.parent_tg)
async def std_save_parent(message: Message, state: FSMContext):
    data = await state.get_data()
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.clear()
    new_parent = message.text.strip() if message.text else None
    await _apply_parent_update(message, lang, data, new_parent)


@router.callback_query(StudentEdit.parent_tg, F.data == "std_skip_parent")
async def std_skip_parent_edit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.clear()
    await _apply_parent_update(call.message, lang, data, None, edit=True)
    await call.answer()


async def _apply_parent_update(msg, lang: str, data: dict, new_parent, edit: bool = False):
    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id == data["student_id"]).first()
        if not s:
            await msg.answer(T(lang, "error"))
            return
        s.parent_telegram_id = new_parent
        db.commit()
        first, last, class_id = s.first_name, s.last_name, s.class_id
        stds = db.query(Student).filter(Student.class_id == class_id).all()
        std_list = [{"id": x.id, "first": x.first_name, "last": x.last_name} for x in stds]
    finally:
        db.close()

    kb = students_list_kb(lang, std_list, data["class_id"])
    text = T(lang, "std_updated", first=first, last=last)
    if edit:
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


# ── O'quvchi qo'shish (StudentAdd FSM) ────────────────────────────────────────

@router.callback_query(F.data.startswith("std_add:"))
async def std_add_start(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    class_id = int(call.data.split(":")[1])
    await state.update_data(class_id=class_id)
    await state.set_state(StudentAdd.first_name)
    await call.message.edit_text(T(lang, "std_add_ask_fname"), parse_mode="HTML")
    await call.answer()


@router.message(StudentAdd.first_name)
async def std_got_fname(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(first_name=message.text.strip())
    await state.set_state(StudentAdd.last_name)
    await message.answer(T(lang, "std_add_ask_lname"), parse_mode="HTML")


@router.message(StudentAdd.last_name)
async def std_got_lname(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    await state.update_data(last_name=message.text.strip())
    await state.set_state(StudentAdd.parent_tg)
    await message.answer(
        T(lang, "std_add_ask_parent"),
        reply_markup=skip_kb(lang),
        parse_mode="HTML",
    )


@router.message(StudentAdd.parent_tg)
async def std_got_parent(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)
    parent_tg = message.text.strip() if message.text else None
    await _std_show_confirm(message, state, lang, parent_tg)


@router.callback_query(StudentAdd.parent_tg, F.data == "std_skip_parent")
async def std_skip_parent(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await _std_show_confirm(call.message, state, lang, None, edit=True)
    await call.answer()


async def _std_show_confirm(msg, state: FSMContext, lang: str, parent_tg, edit: bool = False):
    """Tasdiqlash xabarini ko'rsatish (message yoki callback dan)."""
    await state.update_data(parent_tg=parent_tg)
    data = await state.get_data()
    await state.set_state(StudentAdd.confirm)

    db = SessionLocal()
    try:
        cls = db.query(StudentClass).filter(StudentClass.id == data["class_id"]).first()
        cls_name = cls.name if cls else "?"
    finally:
        db.close()

    await state.update_data(cls_name=cls_name)
    parent_display = parent_tg if parent_tg else "—"
    text = T(
        lang, "std_add_confirm",
        first=data["first_name"],
        last=data["last_name"],
        cls=cls_name,
        parent=parent_display,
    )
    kb = confirm_kb(lang, yes_cb="std_confirm_yes", no_cb="std_confirm_no")
    if edit:
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(StudentAdd.confirm, F.data == "std_confirm_yes")
async def std_save(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await state.clear()

    db = SessionLocal()
    try:
        std = Student(
            first_name=data["first_name"],
            last_name=data["last_name"],
            class_id=data["class_id"],
            parent_telegram_id=data.get("parent_tg"),
        )
        db.add(std)
        db.commit()
        cls_name = data.get("cls_name", "?")
    finally:
        db.close()

    # Saqlagandan keyin o'quvchilar ro'yxatiga qaytamiz
    db2 = SessionLocal()
    try:
        stds = db2.query(Student).filter(Student.class_id == data["class_id"]).all()
        std_list = [{"id": s.id, "first": s.first_name, "last": s.last_name} for s in stds]
    finally:
        db2.close()

    await call.message.edit_text(
        T(lang, "std_add_saved",
          first=data["first_name"], last=data["last_name"], cls=cls_name),
        reply_markup=students_list_kb(lang, std_list, data["class_id"]),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "std_confirm_no")
async def std_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    class_id = data.get("class_id", 0)
    await call.message.edit_text(
        T(lang, "std_add_cancel"),
        reply_markup=class_detail_kb(lang, class_id),
        parse_mode="HTML",
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

    admins = get_bot_admins()
    if admins:
        admin_list = "".join(T(lang, "admin_row", tid=a, name="") for a in admins)
    else:
        admin_list = T(lang, "no_admins") + "\n"

    await call.message.edit_text(
        T(lang, "admins_title", list=admin_list),
        reply_markup=admins_manage_kb(lang, admins, tid),
        parse_mode="HTML",
    )
    await call.answer()


# ── Admin qo'shish ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin_add_start")
async def admin_add_start(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    await state.set_state(AdminAdd.telegram_id)
    await call.message.edit_text(
        T(lang, "admin_add_prompt"),
        reply_markup=back_admin_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.message(AdminAdd.telegram_id)
async def admin_add_get_id(msg: Message, state: FSMContext):
    tid = str(msg.from_user.id)
    lang = _lang(tid)
    new_id = msg.text.strip() if msg.text else ""

    if not new_id.lstrip("-").isdigit():
        await msg.answer(T(lang, "admin_add_invalid"), parse_mode="HTML")
        return

    admins = get_bot_admins()
    if new_id in admins:
        await state.clear()
        await msg.answer(T(lang, "admin_add_exists"), parse_mode="HTML")
        return

    await state.update_data(new_admin_id=new_id)
    await state.set_state(AdminAdd.confirm)
    await msg.answer(
        T(lang, "admin_add_confirm", tid=new_id),
        reply_markup=admin_add_confirm_kb(lang, new_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_add_ok:"))
async def admin_add_ok(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    new_id = call.data.split(":", 1)[1]
    await state.clear()
    add_bot_admin(new_id)

    await call.message.edit_text(
        T(lang, "admin_added", tid=new_id),
        parse_mode="HTML",
    )
    # Yangi ro'yxatni ko'rsat
    admins = get_bot_admins()
    admin_list = "".join(T(lang, "admin_row", tid=a, name="") for a in admins) or T(lang, "no_admins") + "\n"
    await call.message.answer(
        T(lang, "admins_title", list=admin_list),
        reply_markup=admins_manage_kb(lang, admins, tid),
        parse_mode="HTML",
    )
    await call.answer()


# ── Admin o'chirish ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_del_ask:"))
async def admin_del_ask(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    del_id = call.data.split(":", 1)[1]
    if del_id == tid:
        await call.answer(T(lang, "admin_del_self"), show_alert=True)
        return

    await call.message.edit_text(
        T(lang, "admin_del_confirm", tid=del_id),
        reply_markup=admin_del_confirm_kb(lang, del_id),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin_del_ok:"))
async def admin_del_ok(call: CallbackQuery):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not _check_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return

    del_id = call.data.split(":", 1)[1]
    removed = remove_bot_admin(del_id)

    if removed:
        await call.message.edit_text(T(lang, "admin_deleted", tid=del_id), parse_mode="HTML")
    else:
        await call.message.edit_text(T(lang, "admin_not_found"), parse_mode="HTML")

    admins = get_bot_admins()
    admin_list = "".join(T(lang, "admin_row", tid=a, name="") for a in admins) or T(lang, "no_admins") + "\n"
    await call.message.answer(
        T(lang, "admins_title", list=admin_list),
        reply_markup=admins_manage_kb(lang, admins, tid),
        parse_mode="HTML",
    )
    await call.answer()
