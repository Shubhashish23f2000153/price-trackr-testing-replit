# backend/app/crud/user.py
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user_schema import UserCreate
from ..utils.auth import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    # This line prevents the crash, no matter what the browser sends
    hashed_password = get_password_hash(user.password[:72]) 
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- ADD THIS NEW FUNCTION ---
def delete_user(db: Session, user_id: int) -> bool:
    """Deletes a user by their ID."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False
# --- END NEW FUNCTION ---