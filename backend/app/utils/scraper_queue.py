from redis import Redis
from rq import Queue
from ..config import settings

redis_conn = Redis.from_url(settings.REDIS_URL)
scraper_queue = Queue("scraping", connection=redis_conn)
scam_queue = Queue("scam_checks", connection=redis_conn)
alert_queue = Queue("alerts", connection=redis_conn) # <-- ADD THIS
sales_queue = Queue("sales_discovery", connection=redis_conn) # <-- ADD THIS
aggregate_queue = Queue("aggregation", connection=redis_conn) # <-- ADD THIS

def enqueue_scrape(url: str, product_id: int, source_id: int):
    """Enqueue a scraping job"""
    job = scraper_queue.enqueue(
        'playwright_scraper.runner.scrape_and_save_product',
        url,
        product_id,
        source_id,
        job_timeout='5m'
    )
    return job.id

def enqueue_scam_check(domain: str):
    """Enqueue a scam check job"""
    job = scam_queue.enqueue(
        'playwright_scraper.runner.compute_scam_score',
        domain,
        job_timeout='5m'
    )
    return job.id

# --- ADD THIS NEW FUNCTION ---
def enqueue_alert_check():
    """Enqueue a job to check all price alerts."""
    job = alert_queue.enqueue(
        'playwright_scraper.runner.check_price_alerts',
        job_timeout='10m'
    )
    return job.id

# --- ADD THIS NEW FUNCTION ---
def enqueue_sales_discovery():
    """Enqueue a job to check for new sales."""
    job = sales_queue.enqueue(
        'playwright_scraper.runner.run_sales_discovery_job',
        job_timeout='15m'
    )
    return job.id

def enqueue_aggregation():
    """Enqueue a job to run price data aggregation."""
    job = aggregate_queue.enqueue(
        'playwright_scraper.runner.run_aggregation_job',
        job_timeout='30m' # Give it time
    )
    return job.id
# --- END NEW FUNCTION ---