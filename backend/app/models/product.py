from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    brand = Column(String(200), nullable=True)
    category = Column(String(200), nullable=True)
    image_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product_sources = relationship("ProductSource", back_populates="product", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="product", cascade="all, delete-orphan")
