# backend/app/models/source.py
# (Added seller_id column and seller relationship to ProductSource)
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, nullable=False, index=True)
    site_name = Column(String(200), nullable=False)
    trust_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product_sources = relationship("ProductSource", back_populates="source")


class ProductSource(Base):
    __tablename__ = "product_sources"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    
    # --- ADDED THIS LINE ---
    seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    
    url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="product_sources")
    source = relationship("Source", back_populates="product_sources")
    
    # --- ADDED THIS LINE ---
    seller = relationship("Seller", back_populates="product_sources")
    
    price_logs = relationship("PriceLog", back_populates="product_source", cascade="all, delete-orphan")

    # --- ADD THESE TWO LINES ---
    price_history_daily = relationship("PriceHistoryDaily", back_populates="product_source", cascade="all, delete-orphan")
    price_history_monthly = relationship("PriceHistoryMonthly", back_populates="product_source", cascade="all, delete-orphan")