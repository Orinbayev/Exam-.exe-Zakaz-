"""
Savollar CRUD endpointlari.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Question, Category, User
from ..schemas import QuestionCreate, QuestionUpdate, QuestionOut, CategoryCreate, CategoryOut
from ..auth import require_teacher_or_admin, get_current_user

router = APIRouter(prefix="/api/questions", tags=["questions"])

# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    if current_user.role == "superadmin":
        return db.query(Category).all()
    return db.query(Category).filter(Category.teacher_id == current_user.id).all()


@router.post("/categories", response_model=CategoryOut)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    cat = Category(name=data.name, teacher_id=current_user.id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ── Questions ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[QuestionOut])
def list_questions(
    category_id: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    q = db.query(Question)
    if current_user.role != "superadmin":
        q = q.filter(Question.teacher_id == current_user.id)
    if category_id:
        q = q.filter(Question.category_id == category_id)
    if difficulty:
        q = q.filter(Question.difficulty == difficulty)
    if search:
        q = q.filter(Question.text.ilike(f"%{search}%"))
    return q.order_by(Question.created_at.desc()).all()


@router.post("/", response_model=QuestionOut)
def create_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    question = Question(
        text=data.text,
        option_a=data.option_a,
        option_b=data.option_b,
        option_c=data.option_c,
        option_d=data.option_d,
        correct_answer=data.correct_answer,
        category_id=data.category_id,
        difficulty=data.difficulty,
        teacher_id=current_user.id
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    q = db.query(Question).filter(Question.id == question_id)
    if current_user.role != "superadmin":
        q = q.filter(Question.teacher_id == current_user.id)
    question = q.first()
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")
    return question


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    q = db.query(Question).filter(Question.id == question_id)
    if current_user.role != "superadmin":
        q = q.filter(Question.teacher_id == current_user.id)
    question = q.first()
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    q = db.query(Question).filter(Question.id == question_id)
    if current_user.role != "superadmin":
        q = q.filter(Question.teacher_id == current_user.id)
    question = q.first()
    if not question:
        raise HTTPException(status_code=404, detail="Savol topilmadi")

    db.delete(question)
    db.commit()
    return {"message": "Savol o'chirildi"}


@router.post("/import/excel")
async def import_from_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Excel fayldan savollarni yuklash."""
    return {"message": "Excel import tayyor - fayl yuklash uchun /api/questions/upload dan foydalaning"}
