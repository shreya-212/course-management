from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Category, User, UserRole
from ..schemas import CategoryCreate, CategoryUpdate, CategoryResponse



router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)