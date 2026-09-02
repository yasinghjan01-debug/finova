from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from apps.api.core.database import get_db
from apps.api.core.auth import hash_password, verify_password, create_access_token, get_current_user
from apps.api.models.schema import User
from apps.api.services.audit_svc import AuditChainService

router = APIRouter(prefix="/auth", tags=["Authentication & User Security"])

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    business_name: Optional[str] = None
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    role: str

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    new_user = User(
        email=clean_email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        business_name=payload.business_name,
        phone=payload.phone,
        role="merchant",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    AuditChainService.record_event(
        db=db,
        user_id=new_user.id,
        event_type="USER_REGISTERED",
        actor="AUTH_SERVICE",
        details={"email": new_user.email, "name": new_user.name}
    )
    
    token = create_access_token(user_id=new_user.id, email=new_user.email, role=new_user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
        
    token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    
    AuditChainService.record_event(
        db=db,
        user_id=user.id,
        event_type="USER_LOGIN_SUCCESS",
        actor="USER",
        details={"email": user.email}
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "business_name": current_user.business_name,
        "phone": current_user.phone,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }
