"""
Statistika endpointlari - diagrammalar va reyting uchun ma'lumot.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import ExamSession, Test, Question, User
from ..auth import require_teacher_or_admin

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Umumiy statistika."""
    q = db.query(ExamSession).filter(ExamSession.is_completed == True)
    if current_user.role != "superadmin":
        test_ids = [t.id for t in current_user.tests]
        q = q.filter(ExamSession.test_id.in_(test_ids))

    sessions = q.all()
    scores = [s.score_percent for s in sessions]

    return {
        "total_sessions": len(sessions),
        "total_passed": sum(1 for s in sessions if s.is_passed),
        "total_failed": sum(1 for s in sessions if not s.is_passed),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "highest_score": round(max(scores), 2) if scores else 0,
        "lowest_score": round(min(scores), 2) if scores else 0,
        "pass_rate": round(sum(1 for s in sessions if s.is_passed) / len(sessions) * 100, 2) if sessions else 0,
        "total_tests": db.query(Test).filter(
            Test.teacher_id == current_user.id if current_user.role != "superadmin" else True
        ).count(),
        "total_questions": db.query(Question).filter(
            Question.teacher_id == current_user.id if current_user.role != "superadmin" else True
        ).count(),
    }


@router.get("/top-students")
def top_students(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Eng yaxshi o'quvchilar reytingi."""
    q = db.query(ExamSession).filter(ExamSession.is_completed == True)
    if current_user.role != "superadmin":
        test_ids = [t.id for t in current_user.tests]
        q = q.filter(ExamSession.test_id.in_(test_ids))

    sessions = q.order_by(ExamSession.score_percent.desc()).limit(limit).all()
    return [{
        "student_name": s.student_name,
        "student_lastname": s.student_lastname,
        "student_class": s.student_class,
        "test_name": s.test.name if s.test else "-",
        "score_percent": s.score_percent,
        "grade": s.grade,
    } for s in sessions]


@router.get("/by-test")
def stats_by_test(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Har bir test bo'yicha statistika."""
    q = db.query(Test)
    if current_user.role != "superadmin":
        q = q.filter(Test.teacher_id == current_user.id)

    tests = q.all()
    result = []
    for test in tests:
        sessions = [s for s in test.sessions if s.is_completed]
        scores = [s.score_percent for s in sessions]
        result.append({
            "test_id": test.id,
            "test_name": test.name,
            "total_attempts": len(sessions),
            "passed": sum(1 for s in sessions if s.is_passed),
            "failed": sum(1 for s in sessions if not s.is_passed),
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        })
    return result


@router.get("/grade-distribution")
def grade_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Baholar taqsimoti."""
    q = db.query(ExamSession).filter(ExamSession.is_completed == True)
    if current_user.role != "superadmin":
        test_ids = [t.id for t in current_user.tests]
        q = q.filter(ExamSession.test_id.in_(test_ids))

    sessions = q.all()
    distribution = {}
    for s in sessions:
        grade = s.grade or "N/A"
        distribution[grade] = distribution.get(grade, 0) + 1
    return distribution


@router.get("/audit-logs")
def audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    from ..models import AuditLog
    q = db.query(AuditLog)
    if current_user.role != "superadmin":
        q = q.filter(AuditLog.user_id == current_user.id)
    logs = q.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "details": l.details,
        "ip_address": l.ip_address,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]
