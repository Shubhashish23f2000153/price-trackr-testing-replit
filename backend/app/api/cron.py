# backend/app/api/cron.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
# --- 1. Import SessionLocal AND Source model ---
from ..database import get_db, SessionLocal
from ..models import ProductSource, Source
from ..utils.scraper_queue import (
    enqueue_scrape, 
    enqueue_alert_check, 
    enqueue_sales_discovery, 
    enqueue_aggregation
)

router = APIRouter()

# --- 2. Remove 'db: Session' argument ---
def run_all_scrapes():
    """Function to be run in the background to enqueue scrapes."""
    
    # --- 3. Create a new session inside the task ---
    with SessionLocal() as db:
        
        # --- THIS IS THE "MEESHO SOUVENIR" FIX ---
        # We join with the Source table and filter out 'meesho.com'
        all_product_sources = db.query(ProductSource).join(
            Source, ProductSource.source_id == Source.id
        ).filter(
            Source.domain != 'meesho.com'
        ).all()
        # --- END OF FIX ---
        
        # This print statement will now appear in your backend logs
        print(f"Found {len(all_product_sources)} products to re-scrape. (Ignoring meesho.com)")
        for ps in all_product_sources:
            try:
                enqueue_scrape(ps.url, ps.product_id, ps.id)
            except Exception as e:
                print(f"Failed to enqueue scrape job for {ps.url}: {e}")

def run_sales_discovery():
    """Function to be run in the background to find sales."""
    try:
        print("Enqueuing sales discovery job.")
        enqueue_sales_discovery()
    except Exception as e:
        print(f"Failed to enqueue sales discovery job: {e}")

def run_alert_checks():
    """Function to be run in the background to check alerts."""
    try:
        print("Enqueuing price alert check job.")
        enqueue_alert_check()
    except Exception as e:
        print(f"Failed to enqueue alert check job: {e}")

def run_data_aggregation():
    """Function to be run in the background to aggregate data."""
    try:
        print("Enqueuing data aggregation job.")
        enqueue_aggregation()
    except Exception as e:
        print(f"Failed to enqueue data aggregation job: {e}")

@router.post("/trigger-scrapes")
async def trigger_scrapes(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    This endpoint is called by the cron job service.
    It adds scraping, alert checking, sales, AND aggregation to the background.
    """
    print("Cron job triggered: Starting all scrapes, alerts, sales, and aggregation.")
    
    # --- 4. Call the task without the 'db' argument ---
    background_tasks.add_task(run_all_scrapes)
    background_tasks.add_task(run_alert_checks)
    background_tasks.add_task(run_sales_discovery)
    background_tasks.add_task(run_data_aggregation)
    
    return {"message": "All background jobs (scrape, alerts, sales, aggregation) triggered."}