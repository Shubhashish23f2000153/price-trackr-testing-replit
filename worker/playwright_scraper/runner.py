import os
import sys
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright_scraper.scrapers import get_scraper


def scrape_product(url: str):
    """Worker task to scrape a product"""
    try:
        scraper = get_scraper(url)
        data = scraper.scrape()
        return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


if __name__ == "__main__":
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)
    
    # Create queue
    queue = Queue("scraping", connection=redis_conn)
    
    # Start worker
    worker = Worker([queue], connection=redis_conn)
    print("🚀 Scraper worker started...")
    worker.work()
