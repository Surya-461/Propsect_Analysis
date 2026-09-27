from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None       # Google Identity Services ID Token (JWT)
    access_token: Optional[str] = None     # Google OAuth 2.0 Access Token
    email: Optional[EmailStr] = None       # Direct verified email payload
    name: Optional[str] = None             # User's full name
    picture: Optional[str] = None          # Profile picture URL
    google_id: Optional[str] = None        # Google user ID (sub)

class UserResponse(BaseModel):
    id: int
    uuid: str
    name: str
    email: str
    role: str
    is_active: bool
    auth_provider: Optional[str] = "local"
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
