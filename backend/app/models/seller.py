# backend/app/models/seller.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String(100), nullable=False)
    seller_external_id = Column(String(200), nullable=True) # Marketplace-specific ID
    seller_name = Column(String(500), nullable=False, index=True)
    
    # Storing as string to match existing data and UI logic
    seller_rating = Column(String(100), nullable=True) 
    review_count = Column(String(100), nullable=True) 
    
    trust_score = Column(Float, default=50.0)
    verified = Column(Boolean, default=False)
    
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product_sources = relationship("ProductSource", back_populates="seller")

    __table_args__ = (
        UniqueConstraint('marketplace', 'seller_external_id', name='_marketplace_seller_id_uc'),
    )