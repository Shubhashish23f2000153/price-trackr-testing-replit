from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from ..database import get_db
from ..schemas.user_schema import UserCreate, UserResponse, UserLogin, Token
from ..crud import user as user_crud
from ..crud import watchlist as crud_watchlist
from ..utils import auth
from ..config import settings
from ..models.user import User
from ..utils.dependencies import get_current_user # Dependency to get logged-in user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # ... (register endpoint remains the same)
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = user_crud.create_user(db=db, user=user)
    return new_user

@router.post("/login", response_model=Token)
async def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # ... (login endpoint remains the same)
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


@router.post("/merge")
async def merge_anonymous_data(
    anonymous_id: str = Header(..., alias="X-Anonymous-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... (merge endpoint remains the same)
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

# --- ADD THIS NEW ENDPOINT ---
@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(
    current_user: User = Depends(get_current_user), # Ensures user is logged in
    db: Session = Depends(get_db)
):
    """Deletes the currently authenticated user."""
    if not current_user:
        # This shouldn't happen if the dependency works correctly, but good practice
        raise HTTPException(status_code=401, detail="Authentication required")

    success = user_crud.delete_user(db, user_id=current_user.id)

    if not success:
        # Should ideally not happen if user exists, maybe DB error?
        raise HTTPException(status_code=500, detail="Could not delete user")

    return {"message": "User account deleted successfully"}
# --- END NEW ENDPOINT ---