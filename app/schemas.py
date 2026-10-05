import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from .models import UserRole


# Auth Schemas

class UserCreate(BaseModel):
    #Schema for user registration.

 
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    #Schema for user login.
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    #Safe user data returned in API responses (no password_hash).
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str