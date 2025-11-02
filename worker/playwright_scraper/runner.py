# worker/playwright_scraper/runner.py
import os
import sys
import json
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import whois
from datetime import datetime, timezone, timedelta
from typing import List, Optional 
from playwright_scraper.sales_discovery import discover_all_sales 
from pywebpush import webpush, WebPushException
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from playwright_scraper.scrapers import get_scraper

# --- FIX: Import from aggregation.py ---
from .aggregation import run_aggregation_jobs

# --- FIX: Import all models from models.py ---
from .models import (
    Base,
    SessionLocal,
    User,
    Product,
    Source,
    Seller,
    ProductSource,
    PriceLog,
    ScamScore,
    Watchlist,
    PriceHistoryDaily,
    PriceHistoryMonthly
)
# --- END MODEL IMPORT ---


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 1. Load Environment ---
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis connection for Pub/Sub
redis_conn = Redis.from_url(REDIS_URL)

# Context manager for database sessions
@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 3. HELPER: Get or Create Seller ---
def get_or_create_seller(db: Session, marketplace: str, seller_name: str, seller_rating: str, review_count: str) -> Optional[Seller]:
    """Upserts a seller in the database."""
    if not seller_name:
        return None
        
    try:
        # Try to find an existing seller by name and marketplace
        existing_seller = db.query(Seller).filter(
            Seller.marketplace == marketplace,
            Seller.seller_name == seller_name
        ).first()

        if existing_seller:
            # Update existing seller's info if it's new
            existing_seller.seller_rating = seller_rating or existing_seller.seller_rating
            existing_seller.review_count = review_count or existing_seller.review_count
            existing_seller.last_seen = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_seller)
            return existing_seller
        else:
            # Create a new seller
            new_seller = Seller(
                marketplace=marketplace,
                seller_name=seller_name,
                seller_rating=seller_rating,
                review_count=review_count
            )
            db.add(new_seller)
            db.commit()
            db.refresh(new_seller)
            return new_seller
    except Exception as e:
        db.rollback()
        print(f"[Worker] Error in get_or_create_seller: {e}")
        return None


# --- 4. The UPDATED Product Scraper Task ---
def scrape_and_save_product(url: str, product_id: int, source_id: int):
    """Worker task to scrape a product, update seller, save price IF changed, and publish."""
    print(f"[Worker] Scraping: {url} (ProductID: {product_id})")
    
    scraper = None
    try:
        scraper = get_scraper(url)
        data = scraper.scrape() 
        
        if not data or not data.get("price") or data.get("price") == 0:
            print(f"[Worker] Scrape failed for {url}: No data or price.")
            return None

        # ... (Sentiment Analysis logic remains the same) ...
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
        # --- End Sentiment Analysis ---


        with get_db_session() as db:
            # --- NEW SELLER LOGIC ---
            product_source = db.query(ProductSource).filter(ProductSource.id == source_id).first()
            if not product_source:
                 print(f"[Worker] ProductSource {source_id} not found. Aborting.")
                 return None

            marketplace_name = scraper.__class__.__name__.replace("Scraper", "")
            seller = get_or_create_seller(
                db,
                marketplace=marketplace_name,
                seller_name=data.get("seller_name"),
                seller_rating=data.get("seller_rating"),
                review_count=data.get("seller_review_count")
            )
            
            # Link ProductSource to the Seller if not already linked or if changed
            if seller and product_source.seller_id != seller.id:
                product_source.seller_id = seller.id
                # db.commit() # Commit will happen below
                print(f"[Worker] Linked ProductSource {source_id} to Seller {seller.id} ({seller.seller_name})")
            # --- END SELLER LOGIC ---

            # --- CHECK IF PRICE CHANGED (FOR LOGGING ONLY) ---
            last_price_log = db.query(PriceLog).filter(
                PriceLog.product_source_id == source_id
            ).order_by(desc(PriceLog.scraped_at)).first()

            new_price_cents = data.get("price", 0)
            
            if last_price_log and last_price_log.price_cents == new_price_cents:
                print(f"[Worker] Price for {product_id} is unchanged (₹{new_price_cents / 100}). Logging anyway for history.")
            else:
                last_price_cents = last_price_log.price_cents if last_price_log else 'N/A'
                print(f"[Worker] Price changed (or is new). Old: {last_price_cents}, New: {new_price_cents}. Saving new log.")
            
            # --- START CORRECTION ---
            # These lines are now OUTSIDE the if/else block, so they
            # will run every single time, fixing the UnboundLocalError.

            # Step 1: Create the new PriceLog
            new_price_log = PriceLog(
                product_source_id=source_id,
                price_cents=new_price_cents,
                currency=data.get("currency", "INR"),
                availability=data.get("availability", "Unknown"),
                in_stock=data.get("in_stock", True),
                avg_review_sentiment=avg_sentiment_score # Save calculated sentiment
            )
            db.add(new_price_log)
            # --- END CORRECTION ---
            
            # Step 2: Update the main Product entry (if needed)
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                product.title = data.get("title") or product.title
                product.image_url = data.get("image_url") or product.image_url
                product.description = data.get("description") or product.description
                product.brand = data.get("brand") or product.brand
            
            db.commit()
            print(f"[Worker] ✅ Success. DB updated for {product.title if product else 'product_id ' + str(product_id)}")
            
            # Step 3: Publish update to Redis
            try:
                # Refresh seller from the product_source relationship
                db.refresh(product_source)
                seller_info = product_source.seller
                
                update_message = json.dumps({
                    "type": "PRICE_UPDATE",
                    "product_id": product_id,
                    "new_price": new_price_cents / 100,
                    "source_id": source_id,
                    "source_name": marketplace_name,
                    # --- UPDATED: Pull seller info from the seller object ---
                    "seller_name": seller_info.seller_name if seller_info else None,
                    "seller_rating": seller_info.seller_rating if seller_info else None,
                    "seller_review_count": seller_info.review_count if seller_info else None,
                    "avg_review_sentiment": avg_sentiment_score
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


# --- 5. Scam Check Task (FIXED) ---
def compute_scam_score(domain: str):
    """Worker task to compute domain scam score using WHOIS."""
    print(f"[Worker] Computing scam score for: {domain}")
    with get_db_session() as db:
        existing_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
        if existing_score:
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            if existing_score.last_checked and existing_score.last_checked > thirty_days_ago:
                 print(f"[Worker] Score for {domain} is recent. Skipping.")
                 return
            print(f"[Worker] Refreshing score for {domain}.")
        else:
            print(f"[Worker] No score found for {domain}. Computing new score.")

        score = 50.0 
        days_old = None
        
        # --- FIX: This variable will hold the numeric signal ---
        trust_signal_value = None 

        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0] if creation_date else None
            
            if creation_date:
                now_utc = datetime.now(timezone.utc)
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                days_old = (now_utc - creation_date).days
                trust_signal_value = days_old # Store the number
                
                if days_old < 90: score = 20.0
                elif days_old < 365: score = 45.0
                else: score = 80.0
            else:
                 score = 40.0
                 trust_signal_value = -1.0 # Use -1 to indicate "Not Found"
            
            if existing_score:
                 existing_score.whois_days_old = days_old
                 existing_score.score = score
                 existing_score.trust_signals = trust_signal_value # Save the number
                 existing_score.last_checked = datetime.now(timezone.utc)
                 print(f"[Worker] ✅ Success. Updated score for {domain}: {score}")
            else:
                 new_score = ScamScore(
                     domain=domain,
                     whois_days_old=days_old,
                     safe_browsing_flag=False,
                     trust_signals=trust_signal_value, # Save the number
                     score=score
                 )
                 db.add(new_score)
                 print(f"[Worker] ✅ Success. Saved new score for {domain}: {score}")
            db.commit()
        except Exception as e:
            import traceback
            print(f"[Worker] ❌ CRITICAL ERROR checking WHOIS for {domain}: {e}\n{traceback.format_exc()}")
            # Rollback any failed transaction
            db.rollback()
            if not existing_score:
                try:
                    # Try to add a default score so we don't re-check on every run
                    default_score = ScamScore(domain=domain, score=50.0, trust_signals=-1.0) # Use -1
                    db.add(default_score)
                    db.commit()
                except Exception as e2:
                    print(f"[Worker] ❌ Failed to save default score: {e2}")
                    db.rollback()
            elif existing_score:
                 try:
                    existing_score.last_checked = datetime.now(timezone.utc)
                    db.commit()
                 except Exception as e3:
                    print(f"[Worker] ❌ Failed to update last_checked: {e3}")
                    db.rollback()
            return
# --- END FIX ---
        
# --- 6. Price Alert Check Task (remains the same) ---
def check_price_alerts():
    """
    Worker task to check all active price alerts against the latest prices.
    """
    print("[Worker] Checking all active price alerts...")
    triggered_alerts = 0
    with get_db_session() as db:
        items_to_check = db.query(Watchlist).filter(
            Watchlist.alert_rules != None
        ).all()
        print(f"[Worker] Found {len(items_to_check)} watchlist items with alert rules.")
        for item in items_to_check:
            try:
                alert_price = item.alert_rules.get("threshold")
                user_email = item.user_id 
                if not alert_price or not user_email:
                    continue
                product_sources = db.query(ProductSource).filter(ProductSource.product_id == item.product_id).all()
                if not product_sources: continue
                lowest_current_price = None
                for ps in product_sources:
                    latest_price_log = db.query(PriceLog).filter(
                        PriceLog.product_source_id == ps.id
                    ).order_by(desc(PriceLog.scraped_at)).first()
                    if latest_price_log:
                        current_price = latest_price_log.price_cents / 100
                        if lowest_current_price is None or current_price < lowest_current_price:
                            lowest_current_price = current_price
                if lowest_current_price and lowest_current_price <= alert_price:
                    print(f"[Worker]  TRIGGER! Product {item.product_id} is {lowest_current_price}, below alert of {alert_price} for user {item.user_id}")
                    alert_message = json.dumps({
                        "type": "PRICE_ALERT",
                        "product_id": item.product_id,
                        "user_id": user_email,
                        "current_price": lowest_current_price,
                        "alert_price": alert_price
                    })
                    redis_conn.publish("price_updates", alert_message)
                    triggered_alerts += 1
                    user = db.query(User).filter(User.email == user_email).first()
                    if user and user.push_subscription:
                        print(f"[Worker]  Found push subscription for {user_email}. Sending push...")
                        try:
                            vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
                            vapid_claims = {"sub": f"mailto:{os.getenv('VAPID_CLAIMS_EMAIL')}"}
                            payload = json.dumps({
                                "title": "Price Alert!",
                                "body": f"Price for Product ID {item.product_id} dropped to ₹{lowest_current_price}!",
                                "url": f"/product/{item.product_id}"
                            })
                            webpush(
                                subscription_info=user.push_subscription,
                                data=payload,
                                vapid_private_key=vapid_private_key,
                                vapid_claims=vapid_claims
                            )
                            print(f"[Worker]  ✅ Push notification sent.")
                        except WebPushException as ex:
                            print(f"[Worker]  ❌ Error sending push: {ex}")
                            if ex.response and ex.response.status_code in [404, 410]:
                                print(f"[Worker]  Subscription for {user_email} is invalid. Removing.")
                                user.push_subscription = None
                                db.commit()
                        except Exception as e:
                            print(f"[Worker]  ❌ Unexpected error during webpush: {e}")
            except Exception as e:
                print(f"[Worker] Error checking alert for item {item.id}: {e}")
    print(f"[Worker] Finished alert check. Triggered {triggered_alerts} alerts.")
    return triggered_alerts


# --- 7. Sales Discovery Task (remains the same) ---
def run_sales_discovery_job():
    """Worker task to discover and add new sales."""
    print("[Worker] Running sales discovery job...")
    try:
        discover_all_sales()
        print("[Worker] ✅ Sales discovery job complete.")
    except Exception as e:
        print(f"[Worker] ❌ CRITICAL ERROR in sales discovery: {e}")

# --- 8. Aggregation Task ---
def run_aggregation_job():
    """Worker task to run daily and monthly aggregations."""
    print("[Worker] Running price aggregation job...")
    try:
        from .aggregation import run_aggregation_jobs
        run_aggregation_jobs()
        print("[Worker] ✅ Price aggregation job complete.")
    except Exception as e:
        import traceback
        print(f"[Worker] ❌ CRITICAL ERROR in price aggregation: {e}\n{traceback.format_exc()}")


# --- Main Worker Execution ---
if __name__ == "__main__":
    # Create queues
    scraper_queue = Queue("scraping", connection=redis_conn)
    scam_queue = Queue("scam_checks", connection=redis_conn)
    alert_queue = Queue("alerts", connection=redis_conn)
    sales_queue = Queue("sales_discovery", connection=redis_conn)
    aggregate_queue = Queue("aggregation", connection=redis_conn)

    # Start worker for all queues
    worker = Worker(
        [scraper_queue, scam_queue, alert_queue, sales_queue, aggregate_queue],
        connection=redis_conn
    )
    print("🚀 Scraper worker started... Listening for jobs on 'scraping', 'scam_checks', 'alerts', 'sales_discovery', and 'aggregation'.")
    worker.work()