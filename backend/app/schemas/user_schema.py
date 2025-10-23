# backend/app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Base model for user properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Schema for user creation
class UserCreate(UserBase):
    password: str

# Schema for user login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Schema for user response (what's sent back)
class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

# Schema for the auth token
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for token data (payload)
class TokenData(BaseModel):
    email: Optional[str] = None