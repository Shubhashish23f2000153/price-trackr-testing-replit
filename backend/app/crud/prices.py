from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from datetime import datetime, timedelta
from ..models import PriceLog, ProductSource
from ..schemas.price import PriceLogCreate


def create_price_log(db: Session, price: PriceLogCreate) -> PriceLog:
    db_price = PriceLog(**price.model_dump())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def get_price_history(db: Session, product_id: int, days: int = 30) -> List[PriceLog]:
    """Get price history for a product across all sources"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    return db.query(PriceLog).join(ProductSource).filter(
        ProductSource.product_id == product_id,
        PriceLog.scraped_at >= since_date
    ).order_by(PriceLog.scraped_at).all()


def get_lowest_price(db: Session, product_id: int):
    """Get the lowest price ever recorded for a product"""
    result = db.query(func.min(PriceLog.price_cents)).join(ProductSource).filter(
        ProductSource.product_id == product_id
    ).scalar()
    
    return result / 100 if result else None


def get_current_prices(db: Session, product_id: int):
    """Get current prices from all sources for a product"""
    product_sources = db.query(ProductSource).filter(
        ProductSource.product_id == product_id
    ).all()
    
    prices = []
    for ps in product_sources:
        latest = db.query(PriceLog).filter(
            PriceLog.product_source_id == ps.id
        ).order_by(desc(PriceLog.scraped_at)).first()
        
        if latest:
            prices.append({
                "source": ps.source.site_name,
                "price": latest.price_cents / 100,
                "currency": latest.currency,
                "url": ps.url,
                "scraped_at": latest.scraped_at
            })
    
    return prices
