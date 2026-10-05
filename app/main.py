import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from .database import Base, engine, get_db
from .models import User
from .schemas import UserCreate, UserLogin, UserResponse, MessageResponse
from .auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user,
    REFRESH_COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_HTTPONLY,
    COOKIE_SECURE,
    COOKIE_SAMESITE,
)
from jose import JWTError

# Path to the frontend directory (sibling of the app/ package)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"



Base.metadata.create_all(bind=engine)



app = FastAPI(title="Coursely API", version="1.0.0")


# CORS middleware

# Origins allowed to make credentialed requests.

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,         # required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# POST /auth/register  
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):


    # Check if email already exists
    existing = db.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
       
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# POST /auth/login 

@app.post("/auth/login", response_model=UserResponse)
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Log in and receive access + refresh tokens as HttpOnly cookies.

    Inactive users are rejected with 403.
    """

    db_user = authenticate_user(user.email, user.password, db)

    # Create tokens
    access_token = create_access_token(db_user.id, db_user.role)
    refresh_token = create_refresh_token(db_user.id)

    # Set cookies on the response
    set_auth_cookies(response, access_token, refresh_token)

    return db_user


# POST /auth/refresh  
@app.post("/auth/refresh", response_model=MessageResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """Use the refresh token cookie to obtain a new access token."""

    token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing",
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Must be a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Convert the JWT subject back to UUID for database lookup
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload — malformed user ID",
        )

    # Verify the user still exists and is active
    user = db.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Issue new access token and set cookie
    new_access_token = create_access_token(user.id, user.role)
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {"message": "Access token refreshed successfully"}


# GET /auth/me  
@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's info."""
    return current_user


# POST /auth/logout  
@app.post("/auth/logout", response_model=MessageResponse)
def logout(response: Response):
    """Clear authentication cookies."""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# Serve the frontend  (must be AFTER all API routes)
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def serve_index():
    """Serve the frontend SPA."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount frontend static files (CSS, JS) — placed last so it doesn't shadow API routes
app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend-static")