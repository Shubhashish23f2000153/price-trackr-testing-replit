from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, PriceLog
from ..schemas.stats import SpaceInfo

router = APIRouter()

@router.get("/space", response_model=SpaceInfo)
async def get_space_info(db: Session = Depends(get_db)):
    """Get statistics about database usage."""
    tracked_items = db.query(Product).count()
    price_points = db.query(PriceLog).count()
    
    return {
        "tracked_items": tracked_items,
        "price_points": price_points
    }