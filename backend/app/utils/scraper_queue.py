from redis import Redis
from rq import Queue
from ..config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
scraper_queue = Queue("scraping", connection=redis_conn)


def enqueue_scrape(url: str, product_id: int, source_id: int):
    """Enqueue a scraping job"""
    job = scraper_queue.enqueue(
        'playwright_scraper.runner.scrape_product',
        url,
        job_timeout='5m'
    )
    return job.id
