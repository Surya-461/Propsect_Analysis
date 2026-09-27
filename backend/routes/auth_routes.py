import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import UserSignup, UserLogin, UserResponse, TokenResponse, GoogleAuthRequest
from auth.security import get_password_hash, verify_password
from auth.jwt import create_access_token
from auth.dependencies import get_current_user
from auth.google_auth import authenticate_google_user
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])

@router.post("/auth/signup", response_model=TokenResponse)
def signup(req: UserSignup, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    existing_user = UserRepository.get_by_email(db, clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please login instead."
        )

    new_user = UserRepository.create(
        db=db,
        name=req.name.strip(),
        email=clean_email,
        password_hash=get_password_hash(req.password),
        role="user",
        is_active=True
    )

    access_token = create_access_token(data={
        "sub": str(new_user.uuid),
        "email": new_user.email,
        "role": new_user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/auth/login", response_model=TokenResponse)
def login(req: UserLogin, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = UserRepository.get_by_email(db, clean_email)
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact administrator."
        )

    access_token = create_access_token(data={
        "sub": str(user.uuid),
        "email": user.email,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/auth/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_google_user(req, db)
        access_token = create_access_token(data={
            "sub": str(user.uuid),
            "email": user.email,
            "role": user.role
        })
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google Authentication Error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )

@router.get("/auth/me", response_model=UserResponse)
def get_me_auth(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/auth/logout")
def logout():
    """Client-side token disposal confirmation endpoint."""
    return {"status": "success", "message": "Successfully logged out."}


