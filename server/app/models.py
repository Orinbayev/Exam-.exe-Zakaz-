"""
SQLAlchemy ORM modellari - barcha jadvallar.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """Tizim foydalanuvchilari: superadmin, teacher"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # superadmin | teacher
    is_active = Column(Boolean, default=True)
    telegram_chat_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = relationship("Question", back_populates="teacher", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="teacher", cascade="all, delete-orphan")
    logs = relationship("AuditLog", back_populates="user")


class Category(Base):
    """Savol kategoriyalari"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User")
    questions = relationship("Question", back_populates="category")


class Question(Base):
    """Test savollari"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)  # A, B, C, D
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    difficulty = Column(String(10), default="medium")  # easy|medium|hard
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User", back_populates="questions")
    category = relationship("Category", back_populates="questions")
    test_questions = relationship("TestQuestion", back_populates="question")


class Test(Base):
    """Test (bir nechta savollar to'plami)"""
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time_limit = Column(Integer, default=30)        # daqiqalarda
    pass_percent = Column(Float, default=60.0)      # o'tish foizi
    grade_settings = Column(JSON, default=lambda: {"5": 90, "4": 70, "3": 50, "2": 0})
    shuffle_questions = Column(Boolean, default=False)
    shuffle_answers = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User", back_populates="tests")
    test_questions = relationship("TestQuestion", back_populates="test",
                                  order_by="TestQuestion.order_num", cascade="all, delete-orphan")
    sessions = relationship("ExamSession", back_populates="test")


class TestQuestion(Base):
    """Test va savol orasidagi bog'lanish"""
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    order_num = Column(Integer, default=0)

    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question", back_populates="test_questions")


class ExamSession(Base):
    """O'quvchi tomonidan yechilgan test sessiyasi"""
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_name = Column(String(100), nullable=False)
    student_lastname = Column(String(100), nullable=False)
    student_class = Column(String(20), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    answers = Column(JSON, default=dict)     # {str(question_id): "A"|"B"|"C"|"D"}
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    score_percent = Column(Float, default=0.0)
    grade = Column(String(5), nullable=True)
    is_passed = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)

    test = relationship("Test", back_populates="sessions")


class AuditLog(Base):
    """Tizim harakatlari jurnali"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")


class SystemSettings(Base):
    """Tizim sozlamalari (key-value)"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentClass(Base):
    """O'quvchilar sinflari"""
    __tablename__ = "student_classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # "9-A", "10-B"
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User")
    students = relationship("Student", back_populates="student_class",
                            cascade="all, delete-orphan")


class Student(Base):
    """O'quvchi ma'lumotlari"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey("student_classes.id"), nullable=False)
    parent_telegram_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student_class = relationship("StudentClass", back_populates="students")
