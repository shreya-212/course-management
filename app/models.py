import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import mapped_column, Mapped

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