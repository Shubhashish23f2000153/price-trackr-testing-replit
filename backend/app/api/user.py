from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from ..database import get_db
from ..schemas.user_schema import UserCreate, UserResponse, UserLogin, Token
from ..crud import user as user_crud
from ..crud import watchlist as crud_watchlist # Import watchlist crud
from ..utils import auth
from ..config import settings
from ..models.user import User
from ..utils.dependencies import get_current_user # Import the dependency

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = user_crud.create_user(db=db, user=user)
    return new_user

@router.post("/login", response_model=Token)
async def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)):
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

# --- ADD THIS NEW MERGE ENDPOINT ---
@router.post("/merge")
async def merge_anonymous_data(
    anonymous_id: str = Header(..., alias="X-Anonymous-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Merge data from an anonymous ID to the currently logged-in user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="User must be logged in to merge data")

    if not anonymous_id:
        raise HTTPException(status_code=400, detail="Anonymous ID is required")

    user_identifier = current_user.email

    merged_count = crud_watchlist.merge_watchlist(db, anonymous_id, user_identifier)

    return {
        "message": "Data merged successfully",
        "merged_items": merged_count
    }