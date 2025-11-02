from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product, Sale, PriceLog, ProductSource
from ..schemas.stats import SpaceInfo
from sqlalchemy import func, desc, select, cast, Date
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get statistics for the main dashboard."""
    
    total_products = db.query(Product).count()
    active_deals = db.query(Sale).filter(Sale.is_active == True).count()
    
    # --- THIS IS THE NEW, CORRECTED LOGIC FOR PRICE DROPS ---
    
    # 1. Define "today"
    today = datetime.now(timezone.utc).date()

    # 2. Create a subquery to rank prices for each product source
    price_rank_sq = select(
        PriceLog.product_source_id,
        PriceLog.price_cents,
        cast(PriceLog.scraped_at, Date).label("scraped_date"),
        func.row_number().over(
            partition_by=PriceLog.product_source_id,
            order_by=desc(PriceLog.scraped_at)
        ).label("rn")
    ).alias("price_rank")

    # 3. Create a query to get the latest (rn=1) and previous (rn=2) price
    latest_price_q = select(
        price_rank_sq.c.product_source_id,
        price_rank_sq.c.price_cents,
        price_rank_sq.c.scraped_date
    ).where(price_rank_sq.c.rn == 1).alias("latest_price")
    
    prev_price_q = select(
        price_rank_sq.c.product_source_id,
        price_rank_sq.c.price_cents
    ).where(price_rank_sq.c.rn == 2).alias("prev_price")

    # 4. Join them and count where the latest price is from today AND is less than the previous price
    price_drops_query = select(func.count()).select_from(latest_price_q).join(
        prev_price_q,
        latest_price_q.c.product_source_id == prev_price_q.c.product_source_id
    ).where(
        latest_price_q.c.scraped_date == today,
        latest_price_q.c.price_cents < prev_price_q.c.price_cents
    )
    
    price_drops = db.execute(price_drops_query).scalar_one() or 0
    
    # --- END OF NEW LOGIC ---

    return {
        "total_products": total_products,
        "active_deals": active_deals,
        "price_drops": price_drops,
        "total_saved": 0 # Placeholder, this requires more complex logic
    }


@router.get("/space", response_model=SpaceInfo)
async def get_space_info(db: Session = Depends(get_db)):
    """Get statistics for storage space and item counts."""
    tracked_items = db.query(Product).count()
    
    # Count from all price tables for a total
    raw_points = db.query(func.count(PriceLog.id)).scalar()
    daily_points = db.query(func.count("id")).select_from(
        db.query(ProductSource).join(ProductSource.price_history_daily).subquery()
    ).scalar()
    monthly_points = db.query(func.count("id")).select_from(
        db.query(ProductSource).join(ProductSource.price_history_monthly).subquery()
    ).scalar()

    price_points = (raw_points or 0) + (daily_points or 0) + (monthly_points or 0)
    
    return {
        "tracked_items": tracked_items,
        "price_points": price_points
    }