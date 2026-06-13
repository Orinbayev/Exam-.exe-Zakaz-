"""
Autentifikatsiya endpointlari.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, AuditLog
from ..schemas import LoginRequest, Token, UserOut
from ..auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        log = AuditLog(action="login_failed", details=f"username: {data.username}",
                       ip_address=request.client.host if request.client else None)
        db.add(log)
        db.commit()
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akkaunt bloklangan")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    log = AuditLog(user_id=user.id, action="login_success",
                   ip_address=request.client.host if request.client else None)
    db.add(log)
    db.commit()

    return Token(
        access_token=token,
        role=user.role,
        full_name=user.full_name,
        user_id=user.id
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
