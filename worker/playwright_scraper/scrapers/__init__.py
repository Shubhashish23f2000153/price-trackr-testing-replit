from .amazon import AmazonScraper
from .flipkart import FlipkartScraper
# from .ebay import EbayScraper # REMOVED THIS LINE

__all__ = ["AmazonScraper", "FlipkartScraper"] # REMOVED "EbayScraper"

def get_scraper(url: str):
    """Factory function to get appropriate scraper based on URL."""
    hostname = url.lower()
    if "amazon" in hostname or "amzn" in hostname:
        return AmazonScraper(url)
    elif "flipkart" in hostname:
        return FlipkartScraper(url)
    # REMOVED EBAY BLOCK
    # elif "ebay" in hostname:
    #     return EbayScraper(url)
    else:
        raise ValueError(f"No scraper available for URL: {url}")