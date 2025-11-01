# backend/app/api/cron.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProductSource
from ..utils.scraper_queue import (
    enqueue_scrape, 
    enqueue_alert_check, 
    enqueue_sales_discovery, 
    enqueue_aggregation # <-- IMPORT THE CORRECT FUNCTION
)

router = APIRouter()

def run_all_scrapes(db: Session):
    """Function to be run in the background to enqueue scrapes."""
    all_product_sources = db.query(ProductSource).all()
    print(f"Found {len(all_product_sources)} products to re-scrape.")
    for ps in all_product_sources:
        try:
            enqueue_scrape(ps.url, ps.product_id, ps.source_id)
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

# --- THIS IS THE CORRECTED FUNCTION ---
def run_data_aggregation():
    """Function to be run in the background to aggregate data."""
    try:
        print("Enqueuing data aggregation job.")
        enqueue_aggregation() # <-- IT SHOULD CALL enqueue_aggregation()
    except Exception as e:
        print(f"Failed to enqueue data aggregation job: {e}")
# --- END CORRECTION ---

@router.post("/trigger-scrapes")
async def trigger_scrapes(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    This endpoint is called by the cron job service.
    It adds scraping, alert checking, sales, AND aggregation to the background.
    """
    print("Cron job triggered: Starting all scrapes, alerts, sales, and aggregation.")
    
    background_tasks.add_task(run_all_scrapes, db)
    background_tasks.add_task(run_alert_checks)
    background_tasks.add_task(run_sales_discovery)
    background_tasks.add_task(run_data_aggregation) # <-- This line is now correct
    
    return {"message": "All background jobs (scrape, alerts, sales, aggregation) triggered."}