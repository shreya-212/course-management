import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, DateTime, Enum as SAEnum,ForeignKey,UniqueConstraint,func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import mapped_column, Mapped,relationship
from typing import List
from .database import Base


class UserRole(str, enum.Enum):
    #Allowed roles for the platform.
    admin = "admin"
    creator = "creator"
    student = "student"


class User(Base):
    __tablename__ = "users"

    # Primary key — UUID v4
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    full_name: Mapped[str] = mapped_column(index=True)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", create_constraint=True, native_enum=True),
        default=UserRole.student,
        server_default=UserRole.student.value,
    )

    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=None,   
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=None,  
    )
    courses:Mapped[List["Course"]]=relationship(
        "Course",back_populates="creator"
    )

class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"
    
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=None,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=None,
    )
    creator_id:Mapped[uuid.UUID]=mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    creator: Mapped["User"] = relationship("User", back_populates="courses")
    categories:Mapped["Category"]=relationship(
        "Category",back_populates="courses"
    )
    
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )

    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category"
    )

    courses: Mapped[list["Course"]] = relationship(
        back_populates="category"
    )


class Subcategory(Base):
    __tablename__ = "subcategories"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "name",
            name="uq_subcategory_category_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String, nullable=False
    )

    category: Mapped["Category"] = relationship(
        back_populates="subcategories"
    )

    courses: Mapped[list["Course"]] = relationship(
        back_populates="subcategory"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )

    subcategory_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subcategories.id"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String, nullable=False
    )
    subtitle: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    status: Mapped[CourseStatus] = mapped_column(
        SAEnum(CourseStatus, name="coursestatus"),
        default=CourseStatus.draft,
        server_default=CourseStatus.draft.value,
        nullable=False,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    creator: Mapped["User"] = relationship(
        back_populates="courses"
    )

    category: Mapped["Category"] = relationship(
        back_populates="courses"
    )

    subcategory: Mapped["Subcategory"] = relationship(
        back_populates="courses"
    )

    

          