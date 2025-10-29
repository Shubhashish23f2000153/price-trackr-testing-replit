from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProductSource
from ..utils.scraper_queue import enqueue_scrape, enqueue_alert_check # <-- Import new function

router = APIRouter()

def run_all_scrapes(db: Session):
    # ... (this function remains the same)
    all_product_sources = db.query(ProductSource).all()
    print(f"Found {len(all_product_sources)} products to re-scrape.")
    for ps in all_product_sources:
        try:
            enqueue_scrape(ps.url, ps.product_id, ps.source_id)
            print(f"Enqueued scrape for: {ps.url}")
        except Exception as e:
            print(f"Failed to enqueue scrape job for {ps.url}: {e}")

# --- ADD THIS NEW FUNCTION ---
def run_alert_checks():
    """Function to be run in the background to check alerts."""
    try:
        print("Enqueuing price alert check job.")
        enqueue_alert_check()
    except Exception as e:
        print(f"Failed to enqueue alert check job: {e}")

@router.post("/trigger-scrapes")
async def trigger_scrapes(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    This endpoint is called by the cron job service.
    It adds scraping AND alert checking to the background.
    """
    print("Cron job triggered: Starting all scrapes and alert checks.")
    
    # 1. Add scraping task
    background_tasks.add_task(run_all_scrapes, db)
    
    # 2. Add alert check task
    background_tasks.add_task(run_alert_checks)
    
    return {"message": "Scraping and alert check jobs triggered."}