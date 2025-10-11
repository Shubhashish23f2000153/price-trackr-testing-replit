from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.watchlist import WatchlistCreate, WatchlistResponse, WatchlistUpdate # 1. Add WatchlistUpdate
from ..crud import watchlist as crud_watchlist

router = APIRouter()


@router.post("/", response_model=WatchlistResponse)
async def add_to_watchlist(watchlist: WatchlistCreate, db: Session = Depends(get_db)):
    """Add product to watchlist"""
    # Check if already in watchlist
    if crud_watchlist.is_in_watchlist(db, watchlist.product_id):
        # Find the existing item to return it, so UI doesn't break
        item = db.query(crud_watchlist.Watchlist).filter(crud_watchlist.Watchlist.product_id == watchlist.product_id).first()
        return item
    
    db_watchlist = crud_watchlist.create_watchlist_item(db, watchlist)
    return db_watchlist


@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(user_id: str = None, db: Session = Depends(get_db)):
    """Get user's watchlist"""
    items = crud_watchlist.get_watchlist(db, user_id)
    return items


# 2. ADD THIS NEW ENDPOINT
@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_alert(watchlist_id: int, watchlist: WatchlistUpdate, db: Session = Depends(get_db)):
    """Update alert rules for a watchlist item"""
    updated_item = crud_watchlist.update_watchlist_item(db, watchlist_id, watchlist)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return updated_item


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Remove item from watchlist"""
    success = crud_watchlist.delete_watchlist_item(db, watchlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"message": "Removed from watchlist"}