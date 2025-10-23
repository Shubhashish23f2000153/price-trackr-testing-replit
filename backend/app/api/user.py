# backend/app/api/user.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

# Direct imports from schemas, crud, utils, database, config
from ..database import get_db
# CORRECTED IMPORT: Import specific schemas from the user schema file
from ..schemas.user import UserCreate, UserResponse, UserLogin, Token
from ..crud import user as user_crud     # Import user crud functions directly
from ..utils import auth                 # Import auth utils directly
from ..config import settings            # Import settings directly

router = APIRouter()

@router.post("/register", response_model=UserResponse) # Use UserResponse directly
async def register_user(user: UserCreate, db: Session = Depends(get_db)): # Use UserCreate directly
    """Registers a new user."""
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = user_crud.create_user(db=db, user=user)
    return new_user

@router.post("/login", response_model=Token) # Use Token directly
async def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)): # Use UserLogin directly
    """Logs in a user and returns an access token."""
    user = user_crud.get_user_by_email(db, email=user_credentials.email)
    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}