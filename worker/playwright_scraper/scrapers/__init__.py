from .amazon import AmazonScraper
from .flipkart import FlipkartScraper

__all__ = ["AmazonScraper", "FlipkartScraper"]


def get_scraper(url: str):
    """Factory function to get appropriate scraper based on URL"""
    if "amazon" in url.lower():
        return AmazonScraper(url)
    elif "flipkart" in url.lower():
        return FlipkartScraper(url)
    else:
        raise ValueError(f"No scraper available for URL: {url}")
