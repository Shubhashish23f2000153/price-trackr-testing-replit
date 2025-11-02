# --- 1. Import all scrapers ---

# Original IN scrapers
from .amazon import AmazonScraper as AmazonINScraper # Rename original
from .flipkart import FlipkartScraper
from .myntra import MyntraScraper
from .snapdeal import SnapdealScraper
from .meesho import MeeshoScraper
from .vijaysales import VijaySalesScraper # New IN scraper

# US Scrapers
from .amazon_com import AmazonCOMScraper # New US Scraper
from .bestbuy import BestBuyScraper

# UK Scrapers
from .amazon_uk import AmazonUKScraper

# CA Scrapers
from .amazon_ca import AmazonCAScraper
from .bestbuy_ca import BestBuyCAScraper

# AU Scrapers
from .amazon_au import AmazonAUScraper
from .jbhifi import JBHifiScraper

# EU (DE) Scrapers
from .amazon_de import AmazonDEScraper
from .mediamarkt_de import MediaMarktDEScraper
from .saturn_de import SaturnDEScraper

# JP Scrapers
from .rakuten import RakutenScraper
from .yodobashi import YodobashiScraper

# CN Scrapers
from .jd import JDScraper


# --- 2. Add all to __all__ ---
__all__ = [
    "AmazonINScraper", 
    "FlipkartScraper", 
    "MyntraScraper", 
    "SnapdealScraper", 
    "MeeshoScraper",
    "VijaySalesScraper",
    "AmazonCOMScraper",
    "BestBuyScraper",
    "AmazonUKScraper",
    "AmazonCAScraper",
    "BestBuyCAScraper",
    "AmazonAUScraper",
    "JBHifiScraper",
    "AmazonDEScraper",
    "MediaMarktDEScraper",
    "SaturnDEScraper",
    "RakutenScraper",
    "YodobashiScraper",
    "JDScraper"
]

# --- 3. The updated factory function ---
def get_scraper(url: str):
    """Factory function to get appropriate scraper based on URL."""
    hostname = url.lower()
    
    # --- IN Sites ---
    if "flipkart.com" in hostname:
        return FlipkartScraper(url)
    elif "myntra.com" in hostname:
        return MyntraScraper(url)
    elif "snapdeal.com" in hostname:
        return SnapdealScraper(url)
    elif "meesho.com" in hostname:
        return MeeshoScraper(url)
    elif "vijaysales.com" in hostname:
        return VijaySalesScraper(url)
    
    # --- US Sites ---
    elif "bestbuy.com" in hostname:
        return BestBuyScraper(url)
        
    # --- CA Sites ---
    elif "bestbuy.ca" in hostname:
        return BestBuyCAScraper(url)
    
    # --- AU Sites ---
    elif "jbhifi.com.au" in hostname:
        return JBHifiScraper(url)

    # --- EU (DE) Sites ---
    elif "mediamarkt.de" in hostname:
        return MediaMarktDEScraper(url)
    elif "saturn.de" in hostname:
        return SaturnDEScraper(url)
        
    # --- JP Sites ---
    elif "rakuten.co.jp" in hostname:
        return RakutenScraper(url)
    elif "yodobashi.com" in hostname:
        return YodobashiScraper(url)
        
    # --- CN Sites ---
    elif "jd.com" in hostname:
        return JDScraper(url)

    # --- Amazon Domains (Specific first) ---
    elif "amazon.in" in hostname or "amzn.in" in hostname:
        return AmazonINScraper(url)
    elif "amazon.co.uk" in hostname or "amzn.co.uk" in hostname:
        return AmazonUKScraper(url)
    elif "amazon.ca" in hostname or "amzn.ca" in hostname:
        return AmazonCAScraper(url)
    elif "amazon.com.au" in hostname or "amzn.com.au" in hostname:
        return AmazonAUScraper(url)
    elif "amazon.de" in hostname or "amzn.de" in hostname:
        return AmazonDEScraper(url)
    elif "amazon.com" in hostname or "amzn.com" in hostname:
        return AmazonCOMScraper(url) # US is the fallback
        
    else:
        raise ValueError(f"No scraper available for URL: {url}")