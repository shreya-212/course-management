import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr,ConfigDict,HttpUrl

from .models import UserRole,CourseStatus


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

#category schema
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config =ConfigDict(from_attributes=True)


#subcategory schema
class SubcategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class SubcategoryUpdate(BaseModel):
    name: str | None =Field(default=None, min_length=1, max_length=255)


class SubcategoryResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


#course schema
class CourseCreate(BaseModel):
    category_id: uuid.UUID
    subcategory_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    subtitle: str |None = Field(default=None, max_length=255)
    description: str|None = None
    status: CourseStatus = CourseStatus.draft
    thumbnail_url: HttpUrl | None = None


class CourseUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    subcategory_id: uuid.UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    status: CourseStatus | None = None
    thumbnail_url: HttpUrl | None = None

class CourseResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID
    category_id: uuid.UUID
    subcategory_id: uuid.UUID
    title: str
    subtitle: str | None
    description: str | None
    status: CourseStatus
    thumbnail_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class MessageResponse(BaseModel):
    """Generic message response."""
    message: str