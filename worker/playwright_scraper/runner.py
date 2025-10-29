import os
import sys
import json
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float # Import Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from contextlib import contextmanager
import whois
from datetime import datetime, timezone, timedelta
from typing import List # Import List

# --- ADD VADER IMPORT ---
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# --- END VADER IMPORT ---


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright_scraper.scrapers import get_scraper

# --- 1. Load Environment & Database Setup ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pricetrackr:testpassword@localhost:5432/pricetrackr")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Setup database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Define Minimal Database Models ---
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
    product_source_id = Column(Integer, nullable=False) # Changed from ForeignKey for simplicity in worker
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR")
    availability = Column(String(50), default="Unknown")
    in_stock = Column(Boolean, default=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    seller_name = Column(String(200), nullable=True)
    seller_rating = Column(String(100), nullable=True)
    seller_review_count = Column(String(100), nullable=True)
    # --- ADD Sentiment Column ---
    avg_review_sentiment = Column(Float, nullable=True) # Stores avg compound score (-1 to 1)
    # --- End Sentiment Column ---


class ScamScore(Base):
    __tablename__ = "scam_scores"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, nullable=False, index=True)
    whois_days_old = Column(Integer, nullable=True)
    safe_browsing_flag = Column(Boolean, default=False)
    trust_signals = Column(Float, default=0.0) # Simplified for worker
    score = Column(Float, default=0.0)
    last_checked = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Context manager for database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis connection for Pub/Sub
redis_conn = Redis.from_url(REDIS_URL)

# --- 3. The Product Scraper Task ---
def scrape_and_save_product(url: str, product_id: int, source_id: int):
    """Worker task to scrape a product, analyze reviews, AND save data to DB"""
    print(f"[Worker] Scraping: {url} (ProductID: {product_id})")
    try:
        scraper = get_scraper(url)
        data = scraper.scrape() # data is a dict
        
        if not data or not data.get("price") or data.get("price") == 0:
            print(f"[Worker] Scrape failed for {url}: No data or price.")
            return None

        # --- Sentiment Analysis ---
        avg_sentiment_score = None
        reviews = data.get("recent_reviews", [])
        if reviews and isinstance(reviews, list) and len(reviews) > 0:
            analyzer = SentimentIntensityAnalyzer()
            total_compound_score = 0
            valid_reviews_count = 0
            for review_text in reviews:
                if isinstance(review_text, str) and review_text.strip():
                    vs = analyzer.polarity_scores(review_text)
                    total_compound_score += vs['compound']
                    valid_reviews_count += 1
            
            if valid_reviews_count > 0:
                avg_sentiment_score = total_compound_score / valid_reviews_count
                print(f"[Worker] Calculated avg sentiment from {valid_reviews_count} reviews: {avg_sentiment_score:.3f}")
            else:
                print("[Worker] No valid review text found for sentiment analysis.")
        else:
             print("[Worker] No reviews extracted for sentiment analysis.")
        # --- End Sentiment Analysis ---


        with get_db_session() as db:
            # Step 1: Create the new PriceLog
            new_price_log = PriceLog(
                product_source_id=source_id,
                price_cents=data.get("price", 0),
                currency=data.get("currency", "INR"),
                availability=data.get("availability", "Unknown"),
                in_stock=data.get("in_stock", True),
                seller_name=data.get("seller_name"),
                seller_rating=data.get("seller_rating"),
                seller_review_count=data.get("seller_review_count"),
                avg_review_sentiment=avg_sentiment_score # Save calculated sentiment
            )
            db.add(new_price_log)
            
            # Step 2: Update the main Product entry (if needed)
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                # Only update if scraper provided new info
                product.title = data.get("title") or product.title
                product.image_url = data.get("image_url") or product.image_url
                product.description = data.get("description") or product.description
                product.brand = data.get("brand") or product.brand
            
            db.commit()
            print(f"[Worker] ✅ Success. Saved new price & sentiment for {product.title if product else 'product_id ' + str(product_id)}: Price={data.get('price')}, Sentiment={avg_sentiment_score}")
            
            # Step 3: Publish update to Redis (No change needed here for now)
            try:
                update_message = json.dumps({
                    "type": "PRICE_UPDATE",
                    "product_id": product_id,
                    "new_price": new_price_log.price_cents / 100,
                    "source_id": source_id,
                    "source_name": scraper.__class__.__name__.replace("Scraper", ""),
                    # We could add sentiment here if needed for live updates
                })
                redis_conn.publish("price_updates", update_message)
                print(f"[Worker] 📢 Published update to 'price_updates' channel.")
            except Exception as e:
                print(f"[Worker] ❌ Failed to publish to Redis: {e}")
                
        return data # Return original scraped data
    
    except Exception as e:
        import traceback
        print(f"[Worker] ❌ CRITICAL ERROR scraping {url}: {e}\n{traceback.format_exc()}")
        return None


# --- 4. Scam Check Task (remains the same for now) ---
def compute_scam_score(domain: str):
    """Worker task to compute domain scam score using WHOIS."""
    # ... (WHOIS logic remains unchanged) ...
    print(f"[Worker] Computing scam score for: {domain}")
    with get_db_session() as db:
        existing_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
        if existing_score:
            # Simple check: Refresh if older than 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            if existing_score.last_checked and existing_score.last_checked > thirty_days_ago:
                 print(f"[Worker] Score for {domain} is recent. Skipping.")
                 return
            print(f"[Worker] Refreshing score for {domain}.")
        else:
            print(f"[Worker] No score found for {domain}. Computing new score.")


        score = 50.0  # Default score
        days_old = None
        signals = {} # To store evidence/reasons

        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            # Handle cases where creation_date might be a list
            if isinstance(creation_date, list):
                creation_date = creation_date[0] if creation_date else None
            
            if creation_date:
                now_utc = datetime.now(timezone.utc)
                # Ensure creation_date is timezone-aware (assume UTC if not)
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                    
                days_old = (now_utc - creation_date).days
                signals['whois_age_days'] = days_old
                
                # Apply scoring rule based on age
                if days_old < 90: # Less than 3 months
                    score = 20.0 # Suspicious
                elif days_old < 365: # Less than 1 year
                    score = 45.0 # Caution
                else: # Over 1 year
                    score = 80.0 # Looks Good
            else:
                 signals['whois_age_days'] = 'Not Found'
                 score = 40.0 # Caution if age unknown

            # Placeholder for other signals like SSL check, blacklist check etc.
            # signals['ssl_valid'] = True # Example
            # signals['blacklist_check'] = 'clean' # Example
            
            if existing_score:
                 # Update existing record
                 existing_score.whois_days_old = days_old
                 existing_score.score = score
                 existing_score.trust_signals = signals.get('whois_age_days', 0.0) # Update evidence
                 existing_score.last_checked = datetime.now(timezone.utc) # Update check time
                 print(f"[Worker] ✅ Success. Updated score for {domain}: {score}")
            else:
                 # Create new record
                 new_score = ScamScore(
                     domain=domain,
                     whois_days_old=days_old,
                     safe_browsing_flag=False, # Placeholder
                     trust_signals=signals.get('whois_age_days', 0.0), # Store main signal
                     score=score
                 )
                 db.add(new_score)
                 print(f"[Worker] ✅ Success. Saved new score for {domain}: {score}")

            db.commit()


        except Exception as e:
            import traceback
            print(f"[Worker] ❌ CRITICAL ERROR checking WHOIS for {domain}: {e}\n{traceback.format_exc()}")
            # Save a default "unknown" score if error & doesn't exist, update last_checked if it does
            if not existing_score:
                default_score = ScamScore(domain=domain, score=50.0, trust_signals=0.0)
                db.add(default_score)
                db.commit()
            elif existing_score:
                 existing_score.last_checked = datetime.now(timezone.utc) # Update check time even on error
                 db.commit()
            return
        
# --- 4. Price Alert Check Task ---
def check_price_alerts():
    """
    Worker task to check all active price alerts against the latest prices.
    """
    print("[Worker] Checking all active price alerts...")
    
    # We need to import Watchlist and Product here
    # Make sure they are imported from the models
    from sqlalchemy import select, desc
    
    # These models are already defined at the top of your file,
    # but we need Watchlist and ProductSource
    class ProductSource(Base):
        __tablename__ = "product_sources"
        id = Column(Integer, primary_key=True, index=True)
        product_id = Column(Integer, nullable=False)
        url = Column(Text, nullable=True)

    class Watchlist(Base):
        __tablename__ = "watchlists"
        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(String(100), nullable=True)
        product_id = Column(Integer, nullable=False)
        alert_rules = Column(JSON, nullable=True)

    
    triggered_alerts = 0
    with get_db_session() as db:
        # 1. Get all watchlist items that have an alert rule
        items_to_check = db.query(Watchlist).filter(
            Watchlist.alert_rules != None
        ).all()
        
        print(f"[Worker] Found {len(items_to_check)} watchlist items with alert rules.")
        
        for item in items_to_check:
            try:
                alert_price = item.alert_rules.get("threshold")
                if not alert_price:
                    continue
                
                # 2. Find all sources for this product
                product_sources = db.query(ProductSource).filter(
                    ProductSource.product_id == item.product_id
                ).all()

                if not product_sources:
                    continue

                # 3. Find the lowest current price for this product
                lowest_current_price = None
                for ps in product_sources:
                    latest_price_log = db.query(PriceLog).filter(
                        PriceLog.product_source_id == ps.id
                    ).order_by(desc(PriceLog.scraped_at)).first()
                    
                    if latest_price_log:
                        current_price = latest_price_log.price_cents / 100
                        if lowest_current_price is None or current_price < lowest_current_price:
                            lowest_current_price = current_price
                
                # 4. Check if the alert is triggered
                if lowest_current_price and lowest_current_price <= alert_price:
                    print(f"[Worker]  TRIGGER! Product {item.product_id} is {lowest_current_price}, below alert of {alert_price} for user {item.user_id}")
                    
                    # 5. Publish an alert message
                    # We can re-use the 'price_updates' channel
                    alert_message = json.dumps({
                        "type": "PRICE_ALERT",
                        "product_id": item.product_id,
                        "user_id": item.user_id, # So the frontend knows who to notify
                        "current_price": lowest_current_price,
                        "alert_price": alert_price
                    })
                    redis_conn.publish("price_updates", alert_message)
                    triggered_alerts += 1
                    
                    # Optional: Remove the alert rule so it doesn't fire again
                    # item.alert_rules = None
                    # db.commit()

            except Exception as e:
                print(f"[Worker] Error checking alert for item {item.id}: {e}")
                
    print(f"[Worker] Finished alert check. Triggered {triggered_alerts} alerts.")
    return triggered_alerts

# --- Main Worker Execution ---
if __name__ == "__main__":
    # Ensure database tables exist (useful for first run or after clearing volumes)
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables verified/created.")
    except Exception as e:
        print(f"Error verifying/creating database tables: {e}")

    # Create queues
    scraper_queue = Queue("scraping", connection=redis_conn)
    scam_queue = Queue("scam_checks", connection=redis_conn)
    alert_queue = Queue("alerts", connection=redis_conn) # <-- ADD THIS
    
    # Start worker for all queues
    worker = Worker([scraper_queue, scam_queue, alert_queue], connection=redis_conn) # <-- ADD alert_queue
    print("🚀 Scraper worker started... Listening for jobs on 'scraping', 'scam_checks', and 'alerts'.")
    worker.work()