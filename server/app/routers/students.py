"""
Sinflar va o'quvchilar boshqaruvi.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..auth import require_teacher_or_admin
from ..models import User

router = APIRouter(prefix="/api/students", tags=["students"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str  # "9-A", "10-B"

class ClassOut(BaseModel):
    id: int
    name: str
    teacher_id: int
    student_count: int = 0
    model_config = {"from_attributes": True}

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    parent_telegram_id: Optional[str] = None

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    parent_telegram_id: Optional[str] = None

class StudentOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    class_id: int
    parent_telegram_id: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Lazy import helper ────────────────────────────────────────────────────────

def get_models():
    from ..models import StudentClass, Student
    return StudentClass, Student


# ── Classes ───────────────────────────────────────────────────────────────────

@router.get("/classes")
def list_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    q = db.query(StudentClass)
    if current_user.role != "superadmin":
        q = q.filter(StudentClass.teacher_id == current_user.id)
    classes = q.order_by(StudentClass.name).all()
    return [{
        "id": c.id,
        "name": c.name,
        "teacher_id": c.teacher_id,
        "student_count": len(c.students)
    } for c in classes]


@router.get("/classes/public")
def public_classes(db: Session = Depends(get_db)):
    """O'quvchi info oynasi uchun (token talab etilmaydi)."""
    StudentClass, Student = get_models()
    classes = db.query(StudentClass).order_by(StudentClass.name).all()
    return [{"id": c.id, "name": c.name} for c in classes]


@router.post("/classes")
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    cls = StudentClass(name=data.name, teacher_id=current_user.id)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {"id": cls.id, "name": cls.name, "teacher_id": cls.teacher_id, "student_count": 0}


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Sinf topilmadi")
    db.delete(cls)
    db.commit()
    return {"message": "Sinf o'chirildi"}


# ── Students ──────────────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/students")
def list_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    students = db.query(Student).filter(Student.class_id == class_id)\
        .order_by(Student.last_name).all()
    return [{
        "id": s.id,
        "first_name": s.first_name,
        "last_name": s.last_name,
        "class_id": s.class_id,
        "parent_telegram_id": s.parent_telegram_id
    } for s in students]


@router.get("/classes/{class_id}/students/public")
def public_students(class_id: int, db: Session = Depends(get_db)):
    """O'quvchi info oynasi uchun."""
    StudentClass, Student = get_models()
    students = db.query(Student).filter(Student.class_id == class_id)\
        .order_by(Student.last_name).all()
    return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name} for s in students]


@router.post("/classes/{class_id}/students")
def add_student(
    class_id: int,
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    student = Student(
        first_name=data.first_name,
        last_name=data.last_name,
        class_id=class_id,
        parent_telegram_id=data.parent_telegram_id
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "first_name": student.first_name,
            "last_name": student.last_name, "class_id": student.class_id,
            "parent_telegram_id": student.parent_telegram_id}


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return {"id": student.id, "first_name": student.first_name,
            "last_name": student.last_name, "class_id": student.class_id,
            "parent_telegram_id": student.parent_telegram_id}


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student = get_models()
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    db.delete(student)
    db.commit()
    return {"message": "O'quvchi o'chirildi"}
