import uuid
import os
from dotenv import load_dotenv

load_dotenv()

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, Request, Response, status, HTTPException
from .database import get_db
from .models import User, UserRole
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Cookie names
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# Cookie settings (easy to change for production later)
COOKIE_HTTPONLY = True
COOKIE_SECURE = False          # Set True in production (HTTPS)
COOKIE_SAMESITE = "lax"        # "lax" works for local dev; use "none" if cross-site + HTTPS


# Password hashing 


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)





def create_access_token(user_id: uuid.UUID, role: str | UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role if isinstance(role, str) else role.value,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])



# Cookie  


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set access and refresh tokens as HttpOnly cookies on the response."""
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",           # refresh cookie only sent to /auth routes
    )


def clear_auth_cookies(response: Response):
    """Delete both auth cookies."""
    response.delete_cookie(key=ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/auth")


# Authentication dependency  

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Reusable FastAPI dependency.

    Reads the access token from the cookie → verifies it → returns the User.
    Raises 401 if anything is wrong.
    Raises 403 if the user account is deactivated.
    """
    token = request.cookies.get(ACCESS_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — access token cookie missing",
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload — malformed user ID",
        )

    user = db.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Reject inactive users
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


# ---------------------------------------------------------------------------
# Role-checking dependency (reusable for future course/admin routes)
# ---------------------------------------------------------------------------

class RoleChecker:
    """
    FastAPI dependency that restricts access to users with specific roles.

    Usage:
        allow_creator = RoleChecker([UserRole.creator, UserRole.admin])

        @app.get("/creator-only", dependencies=[Depends(allow_creator)])
        def creator_route(): ...
    """

    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


# Pre-built role checkers for convenience
require_admin = RoleChecker([UserRole.admin])
require_creator = RoleChecker([UserRole.creator, UserRole.admin])
require_student = RoleChecker([UserRole.student, UserRole.creator, UserRole.admin])



# Authenticate user (login helper)  —  now checks is_active


def authenticate_user(email: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Reject inactive users at login time
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user