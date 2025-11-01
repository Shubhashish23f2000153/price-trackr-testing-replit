# backend/app/models/price_aggregate.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from ..database import Base

class PriceHistoryDaily(Base):
    __tablename__ = "price_history_daily"

    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False, index=True) # The date (day) of the aggregate
    
    min_cents = Column(Integer, nullable=False)
    max_cents = Column(Integer, nullable=False)
    avg_cents = Column(Integer, nullable=False)
    last_cents = Column(Integer, nullable=False) # The last price seen on that day
    
    currency = Column(String(3), default="INR") # <-- FIX: Was String(3s)
    samples = Column(Integer) # How many raw points were aggregated
    
    # Relationships
    product_source = relationship("ProductSource", back_populates="price_history_daily") # <-- FIX: Added back_populates

    __table_args__ = (
        UniqueConstraint('product_source_id', 'day', name='_daily_product_source_day_uc'),
    )


class PriceHistoryMonthly(Base):
    __tablename__ = "price_history_monthly"

    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    month = Column(Date, nullable=False, index=True) # The first day of the month
    
    min_cents = Column(Integer, nullable=False)
    max_cents = Column(Integer, nullable=False)
    avg_cents = Column(Integer, nullable=False)
    last_cents = Column(Integer, nullable=False) # The last price seen in that month
    
    currency = Column(String(3), default="INR") # <-- FIX: Was String(3s)
    samples = Column(Integer) # How many daily/raw points were aggregated
    
    # Relationships
    product_source = relationship("ProductSource", back_populates="price_history_monthly") # <-- FIX: Added back_populates
    
    __table_args__ = (
        UniqueConstraint('product_source_id', 'month', name='_monthly_product_source_month_uc'),
    )