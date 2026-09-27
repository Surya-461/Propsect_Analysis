from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.jwt import decode_access_token
import logging

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT Bearer token and returns the current authenticated User.
    Uses UUID subject for secure user identity verification.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or not credentials.credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_sub = payload.get("sub")
    email = payload.get("email")

    if not user_sub and not email:
        raise credentials_exception

    # Query user from PostgreSQL by uuid first, then fallback to id or email
    user = None
    if user_sub:
        user = db.query(User).filter(User.uuid == str(user_sub)).first()
        if not user:
            try:
                user = db.query(User).filter(User.id == int(user_sub)).first()
            except (ValueError, TypeError):
                pass

    if not user and email:
        user = db.query(User).filter(User.email.ilike(email)).first()

    if not user or not user.is_active:
        raise credentials_exception

    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Validates that the current user has the 'admin' role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user
