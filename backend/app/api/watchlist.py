from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.watchlist import WatchlistCreate, WatchlistResponse
from ..crud import watchlist as crud_watchlist

router = APIRouter()


@router.post("/", response_model=WatchlistResponse)
async def add_to_watchlist(watchlist: WatchlistCreate, db: Session = Depends(get_db)):
    """Add product to watchlist"""
    db_watchlist = crud_watchlist.create_watchlist_item(db, watchlist)
    return db_watchlist


@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(user_id: str = None, db: Session = Depends(get_db)):
    """Get user's watchlist"""
    items = crud_watchlist.get_watchlist(db, user_id)
    return items


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Remove item from watchlist"""
    success = crud_watchlist.delete_watchlist_item(db, watchlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"message": "Removed from watchlist"}
