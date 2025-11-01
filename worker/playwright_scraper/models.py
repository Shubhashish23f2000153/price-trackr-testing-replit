# worker/playwright_scraper/models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, JSON, desc, func, Index, UniqueConstraint, Date
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pricetrackr:testpassword@localhost:5432/pricetrackr")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- All Model Definitions ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    push_subscription = Column(JSON, nullable=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=True)
    image_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    product_sources = relationship("ProductSource", back_populates="product", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, nullable=False, index=True)
    site_name = Column(String(200), nullable=False)
    product_sources = relationship("ProductSource", back_populates="source")

class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True, index=True)
    marketplace = Column(String(100), nullable=False)
    seller_external_id = Column(String(200), nullable=True)
    seller_name = Column(String(500), nullable=False, index=True)
    seller_rating = Column(String(100), nullable=True) 
    review_count = Column(String(100), nullable=True) 
    trust_score = Column(Float, default=50.0)
    verified = Column(Boolean, default=False)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    product_sources = relationship("ProductSource", back_populates="seller")
    __table_args__ = (
        UniqueConstraint('marketplace', 'seller_external_id', name='_marketplace_seller_id_uc'),
    )

class ProductSource(Base):
    __tablename__ = "product_sources"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True)
    url = Column(Text, nullable=False)
    product = relationship("Product", back_populates="product_sources")
    source = relationship("Source", back_populates="product_sources")
    seller = relationship("Seller", back_populates="product_sources")
    price_logs = relationship("PriceLog", back_populates="product_source", cascade="all, delete-orphan")
    price_history_daily = relationship("PriceHistoryDaily", back_populates="product_source", cascade="all, delete-orphan")
    price_history_monthly = relationship("PriceHistoryMonthly", back_populates="product_source", cascade="all, delete-orphan")

class PriceLog(Base):
    __tablename__ = "price_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    availability = Column(String(50), default="Unknown")
    in_stock = Column(Boolean, default=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    avg_review_sentiment = Column(Float, nullable=True)
    product_source = relationship("ProductSource", back_populates="price_logs")
    __table_args__ = (
        UniqueConstraint('product_source_id', 'scraped_at', name='_product_source_scraped_at_uc'),
    )

class ScamScore(Base):
    __tablename__ = "scam_scores"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, nullable=False, index=True)
    whois_days_old = Column(Integer, nullable=True)
    safe_browsing_flag = Column(Boolean, default=False)
    trust_signals = Column(Float, default=0.0) 
    score = Column(Float, default=0.0)
    last_checked = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True)
    product_id = Column(Integer, nullable=False)
    alert_rules = Column(JSON, nullable=True)

class PriceHistoryDaily(Base):
    __tablename__ = "price_history_daily"
    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False, index=True)
    min_cents = Column(Integer, nullable=False)
    max_cents = Column(Integer, nullable=False)
    avg_cents = Column(Integer, nullable=False)
    last_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    samples = Column(Integer)
    product_source = relationship("ProductSource", back_populates="price_history_daily")
    __table_args__ = (
        UniqueConstraint('product_source_id', 'day', name='_daily_product_source_day_uc'),
    )

class PriceHistoryMonthly(Base):
    __tablename__ = "price_history_monthly"
    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, ForeignKey("product_sources.id", ondelete="CASCADE"), nullable=False)
    month = Column(Date, nullable=False, index=True)
    min_cents = Column(Integer, nullable=False)
    max_cents = Column(Integer, nullable=False)
    avg_cents = Column(Integer, nullable=False)
    last_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    samples = Column(Integer)
    product_source = relationship("ProductSource", back_populates="price_history_monthly")
    __table_args__ = (
        UniqueConstraint('product_source_id', 'month', name='_monthly_product_source_month_uc'),
    )