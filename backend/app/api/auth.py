from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from backend.app.database.models import User
from backend.app.schemas.auth import UserRegister, Token, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if email is already taken
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
        
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login, retrieve access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the current logged-in user."""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    name: str = None, 
    email: str = None, 
    password: str = None, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile details (name, email, password)."""
    if name:
        current_user.full_name = name
    if email and email != current_user.email:
        # Check if new email exists
        dup = db.query(User).filter(User.email == email).first()
        if dup:
            raise HTTPException(status_code=400, detail="Email already in use.")
        current_user.email = email
    if password:
        current_user.hashed_password = get_password_hash(password)
        
    db.commit()
    db.refresh(current_user)
    return current_user
