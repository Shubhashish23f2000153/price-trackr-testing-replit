# backend/app/crud/prices.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, cast, Date, union_all, DateTime # <-- IMPORT ADDED HERE
from typing import List, Dict, Any, Literal
from datetime import datetime, timedelta, timezone # <-- This imports 'datetime'
from ..models import PriceLog, ProductSource, Seller, PriceHistoryDaily, PriceHistoryMonthly
from ..schemas.price import PriceLogCreate

# Type for range parameter
RangeOption = Literal["1h", "6h", "24h", "7d", "30d", "90d", "1y", "all"]

def create_price_log(db: Session, price: PriceLogCreate) -> PriceLog:
    db_price = PriceLog(**price.model_dump())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def get_lowest_price(db: Session, product_id: int):
    """Get the lowest price ever recorded for a product across all sources"""
    
    # We need to check all three tables
    raw_q = db.query(func.min(PriceLog.price_cents)).join(ProductSource).filter(
        ProductSource.product_id == product_id
    )
    daily_q = db.query(func.min(PriceHistoryDaily.min_cents)).join(ProductSource).filter(
        ProductSource.product_id == product_id
    )
    monthly_q = db.query(func.min(PriceHistoryMonthly.min_cents)).join(ProductSource).filter(
        ProductSource.product_id == product_id
    )
    
    results = [q.scalar() for q in [raw_q, daily_q, monthly_q] if q.scalar() is not None]
    
    if not results:
        return None
        
    lowest_cents = min(results)
    return lowest_cents / 100 if lowest_cents else None


def get_flexible_price_history(db: Session, product_id: int, range_option: RangeOption = "30d") -> List[Dict[str, Any]]:
    """
    Get price history for a product, automatically selecting the
    best aggregation table (raw, daily, monthly) based on the range.
    """
    
    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=30) # Default
    
    query_table = PriceLog
    date_column = PriceLog.scraped_at
    price_column = PriceLog.price_cents
    
    # 1. Determine date range and which table to query
    if range_option == "1h":
        from_dt = now - timedelta(hours=1)
    elif range_option == "6h":
        from_dt = now - timedelta(hours=6)
    elif range_option == "24h":
        from_dt = now - timedelta(hours=24)
    elif range_option == "7d":
        from_dt = now - timedelta(days=7)
    elif range_option == "30d":
        from_dt = now - timedelta(days=30)
    elif range_option == "90d":
        from_dt = now - timedelta(days=90)
        query_table = PriceHistoryDaily
        date_column = PriceHistoryDaily.day
        price_column = PriceHistoryDaily.avg_cents
    elif range_option == "1y":
        from_dt = now - timedelta(days=365)
        query_table = PriceHistoryDaily # Daily is fine for 1 year
        date_column = PriceHistoryDaily.day
        price_column = PriceHistoryDaily.avg_cents
    elif range_option == "all":
        # For "all", we query and union all three tables
        return get_full_price_history(db, product_id)

    # 2. Build the query for the selected table
    
    # Base query
    query = db.query(
        date_column.label("date"),
        price_column.label("price_cents"),
        ProductSource.id.label("source_id"),
        Seller.seller_name.label("seller_name")
    ).join(
        ProductSource, query_table.product_source_id == ProductSource.id
    ).join(
        Seller, ProductSource.seller_id == Seller.id, isouter=True # Left join to seller
    ).filter(
        ProductSource.product_id == product_id,
        date_column >= from_dt
    ).order_by(
        date_column.asc()
    )
    
    results = query.all()
    
    # 3. Format the results
    return [
        {
            "date": r.date.isoformat(),
            "price": r.price_cents / 100,
            "source": r.seller_name or "Unknown Seller"
        }
        for r in results
    ]


def get_full_price_history(db: Session, product_id: int) -> List[Dict[str, Any]]:
    """
    Queries and unions all three tables (monthly, daily, raw)
    to get the entire price history for a product.
    """
    print("Running get_full_price_history (Union all tables)")
    
    # Define date cutoffs
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)

    # Query 1: Monthly data (older than 1 year)
    monthly_q = db.query(
        cast(PriceHistoryMonthly.month, DateTime).label("date"), # <-- Error was here
        PriceHistoryMonthly.avg_cents.label("price_cents"),
        ProductSource.id.label("source_id"),
        Seller.seller_name.label("seller_name")
    ).join(
        ProductSource, PriceHistoryMonthly.product_source_id == ProductSource.id
    ).join(
        Seller, ProductSource.seller_id == Seller.id, isouter=True
    ).filter(
        ProductSource.product_id == product_id,
        PriceHistoryMonthly.month < one_year_ago.replace(day=1)
    )

    # Query 2: Daily data (between 30 days and 1 year)
    daily_q = db.query(
        cast(PriceHistoryDaily.day, DateTime).label("date"), # <-- Error was here
        PriceHistoryDaily.avg_cents.label("price_cents"),
        ProductSource.id.label("source_id"),
        Seller.seller_name.label("seller_name")
    ).join(
        ProductSource, PriceHistoryDaily.product_source_id == ProductSource.id
    ).join(
        Seller, ProductSource.seller_id == Seller.id, isouter=True
    ).filter(
        ProductSource.product_id == product_id,
        PriceHistoryDaily.day >= one_year_ago.date(),
        PriceHistoryDaily.day < thirty_days_ago.date()
    )

    # Query 3: Raw data (last 30 days)
    raw_q = db.query(
        PriceLog.scraped_at.label("date"),
        PriceLog.price_cents.label("price_cents"),
        ProductSource.id.label("source_id"),
        Seller.seller_name.label("seller_name")
    ).join(
        ProductSource, PriceLog.product_source_id == ProductSource.id
    ).join(
        Seller, ProductSource.seller_id == Seller.id, isouter=True
    ).filter(
        ProductSource.product_id == product_id,
        PriceLog.scraped_at >= thirty_days_ago
    )

    # Union all three queries
    final_union = union_all(monthly_q, daily_q, raw_q).alias("full_history")
    
    # Select and order
    results = db.query(final_union).order_by(final_union.c.date.asc()).all()

    # Format the results
    return [
        {
            "date": r.date.isoformat(),
            "price": r.price_cents / 100,
            "source": r.seller_name or "Unknown Seller"
        }
        for r in results
    ]

# This old function is now replaced by get_flexible_price_history
# def get_price_history(db: Session, product_id: int, days: int = 30) -> List[PriceLog]:
#    ...