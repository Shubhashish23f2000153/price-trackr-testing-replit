from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, Sale, PriceLog
from ..schemas.stats import SpaceInfo # <-- 1. Import the SpaceInfo schema
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get statistics for the main dashboard."""
    total_products = db.query(Product).count()
    active_deals = db.query(Sale).filter(Sale.is_active == True).count()
    
    # Calculate price drops in the last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    # This is a simplified query for demonstration
    price_drops = db.query(PriceLog).filter(PriceLog.scraped_at >= one_day_ago).count()

    return {
        "total_products": total_products,
        "active_deals": active_deals,
        "price_drops": price_drops,
        "total_saved": 0 # Placeholder, this requires more complex logic
    }

# 2. ADD THIS NEW ENDPOINT
@router.get("/space", response_model=SpaceInfo)
async def get_space_info(db: Session = Depends(get_db)):
    """Get statistics for storage space and item counts."""
    tracked_items = db.query(Product).count()
    price_points = db.query(PriceLog).count()
    
    return {
        "tracked_items": tracked_items,
        "price_points": price_points
    }