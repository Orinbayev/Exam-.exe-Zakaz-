"""
JWT token yaratish va tekshirish, parol hash qilish.
hashlib/PBKDF2 ishlatiladi (bcrypt compatibility muammolarini oldini olish uchun).
"""
import hashlib
import hmac
import os
import base64
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = "smart-exam-system-secret-key-2024-uzbekistan"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

_HASH_ITERATIONS = 260000
_HASH_ALG = "sha256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """PBKDF2 bilan parolni hash qilish."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(_HASH_ALG, password.encode("utf-8"), salt, _HASH_ITERATIONS)
    return base64.b64encode(salt + dk).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Hash tekshirish."""
    try:
        raw = base64.b64decode(hashed.encode("utf-8"))
        salt = raw[:16]
        stored_dk = raw[16:]
        dk = hashlib.pbkdf2_hmac(_HASH_ALG, plain.encode("utf-8"), salt, _HASH_ITERATIONS)
        return hmac.compare_digest(dk, stored_dk)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    raw_id = payload.get("sub")
    if raw_id is None:
        raise HTTPException(status_code=401, detail="Token noto'g'ri")
    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token noto'g'ri")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token noto'g'ri")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi yoki bloklangan")
    return user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Faqat Super Admin uchun")
    return current_user


def require_teacher_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("superadmin", "teacher"):
        raise HTTPException(status_code=403, detail="Ruxsat yo'q")
    return current_user
