from redis import Redis
from rq import Queue
from ..config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
scraper_queue = Queue("scraping", connection=redis_conn)


def enqueue_scrape(url: str, product_id: int, source_id: int):
    """Enqueue a scraping job"""
    # MODIFIED: Pass all arguments to the worker task
    job = scraper_queue.enqueue(
        'playwright_scraper.runner.scrape_and_save_product', # Renamed task
        url,
        product_id,
        source_id,
        job_timeout='5m'
    )
    return job.id