import os
import sys
import json
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from contextlib import contextmanager

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright_scraper.scrapers import get_scraper

# --- 1. Load Environment & Database Setup ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pricetrackr:pricetrackr_password@localhost:5432/pricetrackr")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Setup database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Define Minimal Database Models (must match backend) ---
# We define them here so the worker is independent
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=True)
    image_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PriceLog(Base):
    __tablename__ = "price_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_source_id = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    availability = Column(String(50), default="Unknown")
    in_stock = Column(Boolean, default=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

# Context manager for database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis connection for Pub/Sub (for Fix 3)
redis_conn = Redis.from_url(REDIS_URL)

# --- 3. The New Worker Task ---
def scrape_and_save_product(url: str, product_id: int, source_id: int):
    """Worker task to scrape a product AND save data to DB"""
    print(f"[Worker] Scraping: {url} (ProductID: {product_id})")
    try:
        scraper = get_scraper(url)
        data = scraper.scrape() # data is a dict
        
        if not data or not data.get("price") or data.get("price") == 0:
            print(f"[Worker] Scrape failed for {url}: No data or price.")
            return None

        with get_db_session() as db:
            # Step 1: Create the new PriceLog
            new_price_log = PriceLog(
                product_source_id=source_id,
                price_cents=data.get("price", 0),
                currency=data.get("currency", "INR"),
                availability=data.get("availability", "Unknown"),
                in_stock=data.get("in_stock", True)
            )
            db.add(new_price_log)
            
            # Step 2: Update the main Product entry
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.title = data.get("title", product.title)
                product.image_url = data.get("image_url", product.image_url)
                product.description = data.get("description", product.description)
                # brand is not in worker scraper, but we add it just in case
                product.brand = data.get("brand", product.brand)
            
            db.commit()
            print(f"[Worker] ✅ Success. Saved new price for {product.title}: {data.get('price')}")
            
            # --- 4. Publish update to Redis (for Fix 3) ---
            try:
                update_message = json.dumps({
                    "type": "PRICE_UPDATE",
                    "product_id": product_id,
                    "new_price": new_price_log.price_cents / 100,
                    "source_id": source_id,
                    "source_name": scraper.__class__.__name__.replace("Scraper", ""),
                })
                redis_conn.publish("price_updates", update_message)
                print(f"[Worker] 📢 Published update to 'price_updates' channel.")
            except Exception as e:
                print(f"[Worker] ❌ Failed to publish to Redis: {e}")
                
        return data
    
    except Exception as e:
        print(f"[Worker] ❌ CRITICAL ERROR scraping {url}: {e}")
        return None


if __name__ == "__main__":
    # Create queue
    queue = Queue("scraping", connection=redis_conn)
    
    # Start worker
    worker = Worker([queue], connection=redis_conn)
    print("🚀 Scraper worker started... Listening for jobs.")
    worker.work()