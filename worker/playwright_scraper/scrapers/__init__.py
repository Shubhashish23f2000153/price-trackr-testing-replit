from .amazon import AmazonScraper
from .flipkart import FlipkartScraper
# 1. Import the new scrapers
from .myntra import MyntraScraper
from .snapdeal import SnapdealScraper
from .meesho import MeeshoScraper

# 2. Add them to __all__
__all__ = [
    "AmazonScraper", 
    "FlipkartScraper", 
    "MyntraScraper", 
    "SnapdealScraper", 
    "MeeshoScraper"
]

def get_scraper(url: str):
    """Factory function to get appropriate scraper based on URL."""
    hostname = url.lower()
    if "amazon" in hostname or "amzn" in hostname:
        return AmazonScraper(url)
    elif "flipkart" in hostname:
        return FlipkartScraper(url)
    # 3. Add the new routes
    elif "myntra" in hostname:
        return MyntraScraper(url)
    elif "snapdeal" in hostname:
        return SnapdealScraper(url)
    elif "meesho" in hostname:
        return MeeshoScraper(url)
    else:
        raise ValueError(f"No scraper available for URL: {url}")