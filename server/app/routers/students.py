"""
Sinflar va o'quvchilar boshqaruvi + sinf aktivlashtirish + test bog'lash.
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
    name: str

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    parent_telegram_id: Optional[str] = None

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    parent_telegram_id: Optional[str] = None


def get_models():
    from ..models import StudentClass, Student, ClassTest, ClassFan
    return StudentClass, Student, ClassTest, ClassFan


# ── Classes (teacher) ─────────────────────────────────────────────────────────

@router.get("/classes")
def list_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    q = db.query(StudentClass)
    if current_user.role != "superadmin":
        q = q.filter(StudentClass.teacher_id == current_user.id)
    classes = q.order_by(StudentClass.name).all()
    return [{
        "id": c.id,
        "name": c.name,
        "teacher_id": c.teacher_id,
        "is_active": bool(c.is_active),
        "student_count": len(c.students),
        "test_ids": [ct.test_id for ct in db.query(ClassTest).filter(ClassTest.class_id == c.id).all()]
    } for c in classes]


@router.get("/classes/public")
def public_classes(db: Session = Depends(get_db)):
    """Faqat aktiv sinflar — token talab etilmaydi."""
    StudentClass, Student, ClassTest, ClassFan = get_models()
    classes = (db.query(StudentClass)
               .filter(StudentClass.is_active == True)
               .order_by(StudentClass.name).all())
    return [{"id": c.id, "name": c.name} for c in classes]


@router.post("/classes")
def create_class(
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    cls = StudentClass(name=data.name, teacher_id=current_user.id, is_active=False)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {"id": cls.id, "name": cls.name, "teacher_id": cls.teacher_id,
            "is_active": False, "student_count": 0, "test_ids": []}


@router.put("/classes/{class_id}")
def update_class(
    class_id: int,
    data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Sinf topilmadi")
    cls.name = data.name.strip()
    db.commit()
    return {"id": cls.id, "name": cls.name, "is_active": bool(cls.is_active)}


@router.patch("/classes/{class_id}/toggle-active")
def toggle_class_active(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Sinfni aktiv / noaktiv qilish."""
    StudentClass, Student, ClassTest, ClassFan = get_models()
    cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Sinf topilmadi")
    cls.is_active = not bool(cls.is_active)
    db.commit()
    return {"id": cls.id, "is_active": bool(cls.is_active)}


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Sinf topilmadi")
    # FK bog'liq yozuvlarni avval o'chiramiz
    db.query(ClassFan).filter(ClassFan.class_id == class_id).delete()
    db.query(ClassTest).filter(ClassTest.class_id == class_id).delete()
    db.query(Student).filter(Student.class_id == class_id).delete()
    db.delete(cls)
    db.commit()
    return {"message": "Sinf o'chirildi"}


# ── Class ↔ Test links ────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/tests")
def get_class_tests(class_id: int, db: Session = Depends(get_db)):
    """Sinfga biriktirilgan testlar (public)."""
    StudentClass, Student, ClassTest, ClassFan = get_models()
    from ..models import Test
    links = db.query(ClassTest).filter(ClassTest.class_id == class_id).all()
    result = []
    for lnk in links:
        t = db.query(Test).filter(Test.id == lnk.test_id, Test.is_active == True).first()
        if t:
            result.append({
                "id": t.id,
                "name": t.name,
                "question_count": len(t.test_questions),
                "time_limit": t.time_limit,
            })
    return result


@router.post("/classes/{class_id}/tests/{test_id}")
def assign_test_to_class(
    class_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    existing = db.query(ClassTest).filter(
        ClassTest.class_id == class_id, ClassTest.test_id == test_id
    ).first()
    if existing:
        return {"message": "Allaqachon biriktirilgan"}
    link = ClassTest(class_id=class_id, test_id=test_id)
    db.add(link)
    db.commit()
    return {"message": "Test biriktirildi"}


@router.delete("/classes/{class_id}/tests/{test_id}")
def unassign_test_from_class(
    class_id: int,
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    link = db.query(ClassTest).filter(
        ClassTest.class_id == class_id, ClassTest.test_id == test_id
    ).first()
    if link:
        db.delete(link)
        db.commit()
    return {"message": "Test ajratildi"}


# ── Class ↔ Fan links ────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/fans")
def get_class_fans(class_id: int, db: Session = Depends(get_db)):
    """Sinfga biriktirilgan fanlar — token talab etilmaydi (public)."""
    StudentClass, Student, ClassTest, ClassFan = get_models()
    from ..models import Category
    cf_list = db.query(ClassFan).filter(ClassFan.class_id == class_id).all()
    result = []
    for cf in cf_list:
        cat = db.query(Category).filter(Category.id == cf.fan_id).first()
        if cat:
            result.append({
                "fan_id":    cat.id,
                "fan_name":  cat.name,
                "test_id":   cf.test_id,
                "time_limit": getattr(cat, "time_limit", 30),
            })
    return result


@router.post("/classes/{class_id}/fans/{fan_id}")
def assign_fan_to_class(
    class_id: int,
    fan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    """Fanni sinfga biriktirish — aktiv savollardan test avtomatik yaratiladi."""
    StudentClass, Student, ClassTest, ClassFan = get_models()
    from ..models import Category, Question, Test, TestQuestion

    cat = db.query(Category).filter(Category.id == fan_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Fan topilmadi")

    cls = db.query(StudentClass).filter(StudentClass.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Sinf topilmadi")

    active_qs = (db.query(Question)
                 .filter(Question.category_id == fan_id, Question.is_active == True)
                 .all())
    if not active_qs:
        raise HTTPException(status_code=400, detail="Bu fanda aktiv savollar yo'q! Avval savol qo'shing.")

    existing = db.query(ClassFan).filter(
        ClassFan.class_id == class_id, ClassFan.fan_id == fan_id
    ).first()

    if existing and existing.test_id:
        # Testni yangilash (qayta sync)
        test = db.query(Test).filter(Test.id == existing.test_id).first()
        if test:
            db.query(TestQuestion).filter(TestQuestion.test_id == test.id).delete()
            for i, q in enumerate(active_qs):
                db.add(TestQuestion(test_id=test.id, question_id=q.id, order_num=i))
            test.time_limit = getattr(cat, "time_limit", 30)
            test.name = cat.name
            db.commit()
            return {"message": "Fan yangilandi", "test_id": test.id,
                    "question_count": len(active_qs)}

    # Yangi test yaratish
    test = Test(
        name=cat.name,
        teacher_id=current_user.id,
        time_limit=getattr(cat, "time_limit", 30),
        pass_percent=60.0,
        shuffle_questions=True,
        is_active=True,
    )
    db.add(test)
    db.flush()

    for i, q in enumerate(active_qs):
        db.add(TestQuestion(test_id=test.id, question_id=q.id, order_num=i))

    if existing:
        existing.test_id = test.id
    else:
        db.add(ClassFan(class_id=class_id, fan_id=fan_id, test_id=test.id))

    db.commit()
    return {"message": "Fan biriktirildi", "test_id": test.id,
            "question_count": len(active_qs)}


@router.delete("/classes/{class_id}/fans/{fan_id}")
def unassign_fan_from_class(
    class_id: int,
    fan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    cf = db.query(ClassFan).filter(
        ClassFan.class_id == class_id, ClassFan.fan_id == fan_id
    ).first()
    if cf:
        db.delete(cf)
        db.commit()
    return {"message": "Fan ajratildi"}


# ── All students (barcha sinflardan) ─────────────────────────────────────────

@router.get("/all")
def all_students(
    class_id: Optional[int] = None,
    fan_id:   Optional[int] = None,
    search:   Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    q = db.query(Student, StudentClass).join(StudentClass, Student.class_id == StudentClass.id)
    if class_id:
        q = q.filter(Student.class_id == class_id)
    if fan_id:
        linked_class_ids = [
            r.class_id for r in db.query(ClassFan).filter(ClassFan.fan_id == fan_id).all()
        ]
        q = q.filter(Student.class_id.in_(linked_class_ids))
    if search:
        like = f"%{search.lower()}%"
        from sqlalchemy import func
        q = q.filter(
            func.lower(Student.first_name).like(like) |
            func.lower(Student.last_name).like(like)
        )
    rows = q.order_by(StudentClass.name, Student.last_name, Student.first_name).all()
    return [
        {
            "id": s.id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "parent_telegram_id": s.parent_telegram_id,
            "class_id": s.class_id,
            "class_name": cls.name,
        }
        for s, cls in rows
    ]


# ── Students ──────────────────────────────────────────────────────────────────

@router.get("/classes/{class_id}/students")
def list_students(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    students = (db.query(Student).filter(Student.class_id == class_id)
                .order_by(Student.last_name).all())
    return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name,
             "class_id": s.class_id, "parent_telegram_id": s.parent_telegram_id}
            for s in students]


@router.get("/classes/{class_id}/students/public")
def public_students(class_id: int, db: Session = Depends(get_db)):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    students = (db.query(Student).filter(Student.class_id == class_id)
                .order_by(Student.last_name).all())
    return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name}
            for s in students]


@router.post("/classes/{class_id}/students")
def add_student(
    class_id: int,
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin)
):
    StudentClass, Student, ClassTest, ClassFan = get_models()
    student = Student(first_name=data.first_name, last_name=data.last_name,
                      class_id=class_id, parent_telegram_id=data.parent_telegram_id)
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
    StudentClass, Student, ClassTest, ClassFan = get_models()
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
    StudentClass, Student, ClassTest, ClassFan = get_models()
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    db.delete(student)
    db.commit()
    return {"message": "O'quvchi o'chirildi"}
