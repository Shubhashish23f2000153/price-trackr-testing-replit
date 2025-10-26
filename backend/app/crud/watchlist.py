from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Watchlist
from ..schemas.watchlist import WatchlistCreate, WatchlistUpdate

def create_watchlist_item(db: Session, watchlist: WatchlistCreate) -> Watchlist:
    db_watchlist = Watchlist(**watchlist.model_dump())
    db.add(db_watchlist)
    db.commit()
    db.refresh(db_watchlist)
    return db_watchlist

def get_watchlist(db: Session, user_id: Optional[str] = None) -> List[Watchlist]:
    query = db.query(Watchlist)
    if user_id:
        query = query.filter(Watchlist.user_id == user_id)
    return query.all()

def delete_watchlist_item(db: Session, watchlist_id: int) -> bool:
    item = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

def is_in_watchlist(db: Session, product_id: int, user_id: Optional[str] = None) -> bool:
    query = db.query(Watchlist).filter(Watchlist.product_id == product_id)
    if user_id:
        query = query.filter(Watchlist.user_id == user_id)
    return query.first() is not None

def update_watchlist_item(db: Session, watchlist_id: int, watchlist: WatchlistUpdate) -> Optional[Watchlist]:
    item = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if item:
        item.alert_rules = watchlist.alert_rules
        db.commit()
        db.refresh(item)
        return item
    return None

# --- ADD THIS NEW FUNCTION ---
def merge_watchlist(db: Session, anonymous_id: str, user_id: str) -> int:
    """
    Find all watchlist items for an anonymous_id and assign them to a user_id.
    """
    # Find all product IDs the user already has
    user_product_ids = {
        item.product_id for item in 
        db.query(Watchlist.product_id).filter(Watchlist.user_id == user_id).all()
    }

    # Find anonymous items to merge
    items_to_merge = db.query(Watchlist).filter(
        Watchlist.user_id == anonymous_id
    ).all()

    if not items_to_merge:
        return 0

    merged_count = 0
    for item in items_to_merge:
        if item.product_id not in user_product_ids:
            # If user doesn't have it, transfer ownership
            item.user_id = user_id
            user_product_ids.add(item.product_id) # Add to set to prevent duplicates
            merged_count += 1
        else:
            # If user already has this product, delete the anon entry
            db.delete(item)

    db.commit()
    return merged_count