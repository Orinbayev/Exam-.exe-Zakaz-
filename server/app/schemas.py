"""
Pydantic sxemalari - API so'rov/javob validatsiyasi.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # superadmin | teacher
    telegram_chat_id: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    telegram_chat_id: Optional[str] = None

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    telegram_chat_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str
    teacher_id: int

    model_config = {"from_attributes": True}


# ── Question ──────────────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str   # A, B, C, D
    category_id: Optional[int] = None
    difficulty: str = "medium"

    @field_validator("correct_answer")
    @classmethod
    def validate_answer(cls, v):
        if v.upper() not in ("A", "B", "C", "D"):
            raise ValueError("correct_answer A, B, C yoki D bo'lishi kerak")
        return v.upper()

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: Optional[str] = None
    category_id: Optional[int] = None
    difficulty: Optional[str] = None

class QuestionOut(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    category_id: Optional[int] = None
    difficulty: str
    teacher_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class QuestionForExam(BaseModel):
    """O'quvchiga ko'rinadigan savol (to'g'ri javobsiz)"""
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    model_config = {"from_attributes": True}


# ── Test ──────────────────────────────────────────────────────────────────────

class TestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    time_limit: int = 30
    pass_percent: float = 60.0
    grade_settings: Dict[str, float] = {"5": 90, "4": 70, "3": 50, "2": 0}
    shuffle_questions: bool = False
    shuffle_answers: bool = False

class TestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    time_limit: Optional[int] = None
    pass_percent: Optional[float] = None
    grade_settings: Optional[Dict[str, float]] = None
    shuffle_questions: Optional[bool] = None
    shuffle_answers: Optional[bool] = None
    is_active: Optional[bool] = None

class TestOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    teacher_id: int
    time_limit: int
    pass_percent: float
    grade_settings: Dict[str, Any]
    shuffle_questions: bool
    shuffle_answers: bool
    is_active: bool
    question_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}

class TestDetail(TestOut):
    questions: List[QuestionForExam] = []

class AddQuestionsToTest(BaseModel):
    question_ids: List[int]


# ── Session ───────────────────────────────────────────────────────────────────

class SessionStart(BaseModel):
    test_id: int
    student_name: str
    student_lastname: str
    student_class: str

class SessionStartResponse(BaseModel):
    session_id: int
    test_id: int
    test_name: str
    time_limit: int
    questions: List[QuestionForExam]

class SubmitAnswer(BaseModel):
    question_id: int
    answer: str  # A, B, C, D

class FinishSession(BaseModel):
    answers: Dict[str, str]  # {str(question_id): answer}

class SessionResult(BaseModel):
    session_id: int
    student_name: str
    student_lastname: str
    student_class: str
    test_name: str
    total_questions: int
    correct_count: int
    wrong_count: int
    score_percent: float
    grade: Optional[str]
    is_passed: bool
    time_spent: Optional[int] = None  # sekundlarda


# ── Stats & Results ───────────────────────────────────────────────────────────

class ExamSessionOut(BaseModel):
    id: int
    test_id: int
    student_name: str
    student_lastname: str
    student_class: str
    total_questions: int
    correct_count: int
    wrong_count: int
    score_percent: float
    grade: Optional[str]
    is_passed: bool
    is_completed: bool
    start_time: datetime
    end_time: Optional[datetime]

    model_config = {"from_attributes": True}

class StatsOut(BaseModel):
    total_sessions: int
    total_students: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    total_tests: int
    total_questions: int


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    key: str
    value: str

class TelegramSettings(BaseModel):
    bot_token: str
    notify_teacher: bool = True
    notify_student: bool = False

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}
