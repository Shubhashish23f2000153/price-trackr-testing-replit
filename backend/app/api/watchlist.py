from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas.watchlist import WatchlistCreate, WatchlistResponse, WatchlistUpdate
from ..crud import watchlist as crud_watchlist
from ..utils.dependencies import get_current_user
from ..models.user import User

router = APIRouter()

# --- This dependency gets EITHER a logged-in user's email OR an anonymous ID ---
async def get_user_identifier(
    current_user: Optional[User] = Depends(get_current_user),
    anonymous_id: Optional[str] = Header(None, alias="X-Anonymous-ID")
) -> str:
    if current_user:
        return current_user.email  # Use email as the ID string
    if anonymous_id:
        return anonymous_id
    # This will only happen if the frontend fails to send either header
    raise HTTPException(status_code=401, detail="No authentication or anonymous ID provided")


@router.post("/", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist: WatchlistCreate, 
    identifier: str = Depends(get_user_identifier), # Use new dependency
    db: Session = Depends(get_db)
):
    """Add product to watchlist for either anonymous or logged-in user"""

    watchlist.user_id = identifier # Set the user_id on the item

    if crud_watchlist.is_in_watchlist(db, watchlist.product_id, user_id=identifier):
        item = db.query(crud_watchlist.Watchlist).filter(
            crud_watchlist.Watchlist.product_id == watchlist.product_id,
            crud_watchlist.Watchlist.user_id == identifier
        ).first()
        return item

    db_watchlist = crud_watchlist.create_watchlist_item(db, watchlist)
    return db_watchlist


@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(
    identifier: str = Depends(get_user_identifier), # Use new dependency
    db: Session = Depends(get_db)
):
    """Get user's watchlist (anonymous or logged-in)"""
    items = crud_watchlist.get_watchlist(db, identifier)
    return items


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_alert(
    watchlist_id: int, 
    watchlist: WatchlistUpdate, 
    identifier: str = Depends(get_user_identifier), # Add dependency
    db: Session = Depends(get_db)
):
    """Update alert rules for a watchlist item"""
    item_to_update = db.query(crud_watchlist.Watchlist).filter(crud_watchlist.Watchlist.id == watchlist_id).first()

    if not item_to_update:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if item_to_update.user_id != identifier:
        raise HTTPException(status_code=403, detail="Not authorized to update this item")

    updated_item = crud_watchlist.update_watchlist_item(db, watchlist_id, watchlist)
    return updated_item


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int, 
    identifier: str = Depends(get_user_identifier), # Add dependency
    db: Session = Depends(get_db)
):
    """Remove item from watchlist"""
    item_to_delete = db.query(crud_watchlist.Watchlist).filter(crud_watchlist.Watchlist.id == watchlist_id).first()

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    if item_to_delete.user_id != identifier:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")

    success = crud_watchlist.delete_watchlist_item(db, watchlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Removed from watchlist"}