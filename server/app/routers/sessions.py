"""
Exam sessiya endpointlari - o'quvchilar uchun (token talab etilmaydi).
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import random
from datetime import datetime
from ..database import get_db
from ..models import Test, TestQuestion, ExamSession, Question
from ..schemas import SessionStart, SessionStartResponse, FinishSession, SessionResult, QuestionForExam, QuestionResult
from ..auth import require_teacher_or_admin, get_current_user
from ..models import User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def calculate_grade(score_percent: float, grade_settings: dict) -> str:
    """Baho hisoblash: grade_settings = {"5": 90, "4": 70, "3": 50, "2": 0}"""
    sorted_grades = sorted(grade_settings.items(), key=lambda x: float(x[1]), reverse=True)
    for grade, min_percent in sorted_grades:
        if score_percent >= float(min_percent):
            return grade
    return list(sorted_grades)[-1][0]


@router.post("/start", response_model=SessionStartResponse)
def start_exam(data: SessionStart, db: Session = Depends(get_db)):
    """Exam sessiyasini boshlash."""
    test = db.query(Test).filter(Test.id == data.test_id, Test.is_active == True).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi yoki faol emas")
    if not test.test_questions:
        raise HTTPException(status_code=400, detail="Testda savollar yo'q")

    session = ExamSession(
        test_id=test.id,
        student_name=data.student_name,
        student_lastname=data.student_lastname,
        student_class=data.student_class,
        total_questions=len(test.test_questions),
        answers={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    tqs = sorted(test.test_questions, key=lambda x: x.order_num)
    if test.shuffle_questions:
        random.shuffle(tqs)

    questions = []
    for tq in tqs:
        q = tq.question
        qdata = {
            "id": q.id,
            "text": q.text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
        }
        questions.append(QuestionForExam(**qdata))

    return SessionStartResponse(
        session_id=session.id,
        test_id=test.id,
        test_name=test.name,
        time_limit=test.time_limit,
        questions=questions
    )


@router.post("/{session_id}/finish", response_model=SessionResult)
async def finish_exam(
    session_id: int,
    data: FinishSession,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Examni yakunlash va natijani hisoblash."""
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessiya topilmadi")
    if session.is_completed:
        raise HTTPException(status_code=400, detail="Sessiya allaqachon yakunlangan")

    test = session.test
    tqs = {tq.question_id: tq.question for tq in test.test_questions}

    # Har bir savol uchun natija hisoblash
    ordered_tqs = sorted(test.test_questions, key=lambda x: x.order_num)
    correct = 0
    per_question: list[QuestionResult] = []
    for i, tq in enumerate(ordered_tqs):
        q = tq.question
        given = data.answers.get(str(q.id))
        is_correct = bool(given and given.upper() == q.correct_answer)
        if is_correct:
            correct += 1
        per_question.append(QuestionResult(
            question_num=i + 1,
            question_id=q.id,
            given_answer=given.upper() if given else None,
            correct_answer=q.correct_answer,
            is_correct=is_correct,
        ))

    total = len(ordered_tqs)
    wrong = sum(1 for pq in per_question if pq.given_answer and not pq.is_correct)
    score_percent = (correct / total * 100) if total > 0 else 0.0
    grade = calculate_grade(score_percent, test.grade_settings)
    is_passed = score_percent >= test.pass_percent

    session.answers = data.answers
    session.correct_count = correct
    session.wrong_count = wrong
    session.score_percent = round(score_percent, 2)
    session.grade = grade
    session.is_passed = is_passed
    session.is_completed = True
    session.end_time = datetime.utcnow()
    db.commit()

    # Telegram xabar yuborish (background) — alohida db sessiyasi bilan
    background_tasks.add_task(send_telegram_notification, session.id)

    time_spent = None
    if session.end_time and session.start_time:
        time_spent = int((session.end_time - session.start_time).total_seconds())

    return SessionResult(
        session_id=session.id,
        student_name=session.student_name,
        student_lastname=session.student_lastname,
        student_class=session.student_class,
        test_name=test.name,
        total_questions=total,
        correct_count=correct,
        wrong_count=wrong,
        score_percent=round(score_percent, 2),
        grade=grade,
        is_passed=is_passed,
        time_spent=time_spent,
        answers=per_question,
    )


async def send_telegram_notification(session_id: int):
    """Telegram bot orqali natija yuborish — o'z db sessiyasi bilan."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        from ..telegram_bot import notify_result
        session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
        if session:
            await notify_result(session, db)
    except Exception as e:
        print(f"[Telegram background] xato: {e}")
    finally:
        db.close()


@router.get("/results", dependencies=[])
def get_all_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Barcha natijalar (teacher o'ziniki, superadmin hammani ko'radi)."""
    q = db.query(ExamSession).filter(ExamSession.is_completed == True)
    if current_user.role != "superadmin":
        test_ids = [t.id for t in current_user.tests]
        q = q.filter(ExamSession.test_id.in_(test_ids))

    sessions = q.order_by(ExamSession.end_time.desc()).all()
    result = []
    for s in sessions:
        result.append({
            "id": s.id,
            "test_id": s.test_id,
            "test_name": s.test.name if s.test else "-",
            "student_name": s.student_name,
            "student_lastname": s.student_lastname,
            "student_class": s.student_class,
            "total_questions": s.total_questions,
            "correct_count": s.correct_count,
            "wrong_count": s.wrong_count,
            "score_percent": s.score_percent,
            "grade": s.grade,
            "is_passed": s.is_passed,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
        })
    return result
