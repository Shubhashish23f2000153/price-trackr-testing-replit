# backend/app/models/price_log.py
# (Removed seller columns, avg_review_sentiment remains)
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class PriceLog(Base):
    __tablename__ = "price_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    availability = Column(String(50), default="Unknown")
    in_stock = Column(Boolean, default=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # --- REMOVED SELLER COLUMNS ---
    # seller_name = Column(String(200), nullable=True)
    # seller_rating = Column(String(100), nullable=True)
    # seller_review_count = Column(String(100), nullable=True)

    avg_review_sentiment = Column(Float, nullable=True) # Kept this, as it's about the product reviews, not seller

    # Relationships
    product_source = relationship("ProductSource", back_populates="price_logs")
    
    # --- ADDED UNIQUE CONSTRAINT ---
    __table_args__ = (
        UniqueConstraint('product_source_id', 'scraped_at', name='_product_source_scraped_at_uc'),
    )