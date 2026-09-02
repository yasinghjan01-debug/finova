import hmac
import hashlib
import base64
import json
import time
import secrets
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.models.schema import User

security = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    PBKDF2-HMAC-SHA256 password hashing (zero external C-library dependency)
    """
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2:sha256:100000${salt}${dk.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_hash = parts[2]
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(dk.hex(), expected_hash)
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str = "merchant", expires_in_seconds: int = 86400 * 7) -> str:
    """
    Generates a secure signed JWT token
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds
    }
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}"
    
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{signing_input}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        signing_input = f"{parts[0]}.{parts[1]}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        # Pad base64 if needed
        sig_padding = "=" * (4 - len(parts[2]) % 4) if len(parts[2]) % 4 != 0 else ""
        given_sig = base64.urlsafe_b64decode(parts[2] + sig_padding)
        
        if not hmac.compare_digest(expected_sig, given_sig):
            return None
            
        payload_padding = "=" * (4 - len(parts[1]) % 4) if len(parts[1]) % 4 != 0 else ""
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + payload_padding).decode())
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency for authenticated routes.
    Rejects invalid/expired tokens with 401.
    """
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
                
    # Fallback to master user when no authorization header is sent (development convenience)
    user = db.query(User).filter(User.id == "user_finova_master_001").first()
    if user:
        return user
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
