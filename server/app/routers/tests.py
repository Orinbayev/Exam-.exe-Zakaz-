"""
Testlar CRUD va test-savol bog'lanishi endpointlari.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import copy
from ..database import get_db
from ..models import Test, TestQuestion, Question, User
from ..schemas import (TestCreate, TestUpdate, TestOut, TestDetail,
                       AddQuestionsToTest, QuestionForExam)
from ..auth import require_teacher_or_admin

router = APIRouter(prefix="/api/tests", tags=["tests"])


def _build_test_out(test: Test) -> dict:
    data = {
        "id": test.id,
        "name": test.name,
        "description": test.description,
        "teacher_id": test.teacher_id,
        "time_limit": test.time_limit,
        "pass_percent": test.pass_percent,
        "grade_settings": test.grade_settings,
        "shuffle_questions": test.shuffle_questions,
        "shuffle_answers": test.shuffle_answers,
        "is_active": test.is_active,
        "question_count": len(test.test_questions),
        "created_at": test.created_at,
    }
    return data


@router.get("/", response_model=List[TestOut])
def list_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    q = db.query(Test)
    if current_user.role != "superadmin":
        q = q.filter(Test.teacher_id == current_user.id)
    tests = q.order_by(Test.created_at.desc()).all()
    return [_build_test_out(t) for t in tests]


@router.post("/", response_model=TestOut)
def create_test(
    data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    test = Test(
        name=data.name,
        description=data.description,
        teacher_id=current_user.id,
        time_limit=data.time_limit,
        pass_percent=data.pass_percent,
        grade_settings=data.grade_settings,
        shuffle_questions=data.shuffle_questions,
        shuffle_answers=data.shuffle_answers,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return _build_test_out(test)


@router.get("/{test_id}", response_model=TestDetail)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")
    if current_user.role != "superadmin" and test.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    questions = [QuestionForExam.model_validate(tq.question)
                 for tq in sorted(test.test_questions, key=lambda x: x.order_num)]
    result = _build_test_out(test)
    result["questions"] = questions
    return result


@router.put("/{test_id}", response_model=TestOut)
def update_test(
    test_id: int,
    data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")
    if current_user.role != "superadmin" and test.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(test, field, value)

    db.commit()
    db.refresh(test)
    return _build_test_out(test)


@router.delete("/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")
    if current_user.role != "superadmin" and test.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")

    db.delete(test)
    db.commit()
    return {"message": "Test o'chirildi"}


@router.post("/{test_id}/copy", response_model=TestOut)
def copy_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Testni nusxalash."""
    original = db.query(Test).filter(Test.id == test_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Test topilmadi")

    new_test = Test(
        name=f"{original.name} (nusxa)",
        description=original.description,
        teacher_id=current_user.id,
        time_limit=original.time_limit,
        pass_percent=original.pass_percent,
        grade_settings=copy.deepcopy(original.grade_settings),
        shuffle_questions=original.shuffle_questions,
        shuffle_answers=original.shuffle_answers,
    )
    db.add(new_test)
    db.flush()

    for tq in original.test_questions:
        new_tq = TestQuestion(
            test_id=new_test.id,
            question_id=tq.question_id,
            order_num=tq.order_num
        )
        db.add(new_tq)

    db.commit()
    db.refresh(new_test)
    return _build_test_out(new_test)


@router.post("/{test_id}/questions")
def add_questions(
    test_id: int,
    data: AddQuestionsToTest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Testga savollar qo'shish."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test topilmadi")

    existing_ids = {tq.question_id for tq in test.test_questions}
    max_order = max((tq.order_num for tq in test.test_questions), default=0)

    added = 0
    for qid in data.question_ids:
        if qid not in existing_ids:
            max_order += 1
            tq = TestQuestion(test_id=test.id, question_id=qid, order_num=max_order)
            db.add(tq)
            added += 1

    db.commit()
    return {"message": f"{added} ta savol qo'shildi"}


@router.delete("/{test_id}/questions/{question_id}")
def remove_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    tq = db.query(TestQuestion).filter(
        TestQuestion.test_id == test_id,
        TestQuestion.question_id == question_id
    ).first()
    if not tq:
        raise HTTPException(status_code=404, detail="Topilmadi")
    db.delete(tq)
    db.commit()
    return {"message": "Savol testdan olib tashlandi"}


@router.get("/public/list")
def public_test_list(db: Session = Depends(get_db)):
    """O'quvchilar uchun ochiq testlar ro'yxati (token talab etilmaydi)."""
    tests = db.query(Test).filter(Test.is_active == True).all()
    return [{"id": t.id, "name": t.name, "question_count": len(t.test_questions),
             "time_limit": t.time_limit} for t in tests]
