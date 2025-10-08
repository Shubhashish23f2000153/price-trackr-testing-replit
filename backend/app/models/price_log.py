from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class PriceLog(Base):
    __tablename__ = "price_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    price_cents = Column(Integer, nullable=False)  # Store price in minor currency units
    currency = Column(String(3), default="INR")
    availability = Column(String(50), default="Unknown")
    in_stock = Column(Boolean, default=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    product_source = relationship("ProductSource", back_populates="price_logs")
