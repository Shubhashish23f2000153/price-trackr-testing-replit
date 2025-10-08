from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Watchlist
from ..schemas.watchlist import WatchlistCreate


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
