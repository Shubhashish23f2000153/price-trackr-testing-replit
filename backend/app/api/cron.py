from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ProductSource
from ..utils.scraper_queue import enqueue_scrape

router = APIRouter()

def run_all_scrapes(db: Session):
    """
    Function to be run in the background.
    It fetches all product sources and enqueues a scrape job for each.
    """
    all_product_sources = db.query(ProductSource).all()
    print(f"Found {len(all_product_sources)} products to re-scrape.")
    for ps in all_product_sources:
        try:
            # Enqueue a scrape job for each product URL
            enqueue_scrape(ps.url, ps.product_id, ps.source_id)
            print(f"Enqueued scrape for: {ps.url}")
        except Exception as e:
            print(f"Failed to enqueue scrape job for {ps.url}: {e}")

@router.post("/trigger-scrapes")
async def trigger_scrapes(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    This endpoint is called by the cron job service.
    It adds the scraping task to the background to avoid timeouts.
    """
    print("Cron job triggered: Starting all scrapes.")
    background_tasks.add_task(run_all_scrapes, db)
    return {"message": "Scraping jobs triggered for all products."}