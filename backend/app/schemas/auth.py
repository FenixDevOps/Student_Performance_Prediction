from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2, description="Name must contain at least 2 characters")
    role: str = Field(default="student", description="Role can be 'admin', 'teacher', or 'student'")

class UserLogin(BaseModel):
    username: EmailStr  # OAuth2PasswordRequestForm uses 'username' parameter
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime
    xp_points: int = 0
    current_streak: int = 0

    class Config:
        from_attributes = True
