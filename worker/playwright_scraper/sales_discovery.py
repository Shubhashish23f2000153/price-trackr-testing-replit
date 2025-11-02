import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import traceback
import requests
from datetime import datetime, timezone, timedelta

# --- 1. Import ALL modular scrapers ---
from .sales_scrapers import (
    # IN
    MySmartPriceSalesScraper,
    AmazonSalesScraper,
    FlipkartSalesScraper,
    # US
    AmazonComSalesScraper,
    CnetSalesScraper,
    BestBuySalesScraper, 
    # GB
    TechRadarSalesScraper,
    # AU
    FinderAUSalesScraper,
    GadgetGuyAUSalesScraper,
    # EU
    LesNumeriquesSalesScraper,
    HeiseSalesScraper,
    ChipDESalesScraper,
    # JP
    AsciiJPSalesScraper,
    ImpressWatchSalesScraper,
    # CN
    ITHomeSalesScraper,
    KuaiKeJiSalesScraper
)

# --- 2. Import helper functions from the NEW file ---
from .sales_helpers import (
    post_sale_to_api,
    extract_dates,
    get_platform_from_title,
    PROCESSED_SALES_CACHE
)

# --- 3. Define Constants locally ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/'
}


# --- 4. Updated CURATED_SOURCES (no change from before) ---
CURATED_SOURCES = {
    "IN": [
        {"url": "https://www.digit.in/rss/deals.xml", "type": "rss"},
        {"url": "https://www.gadgets360.com/rss/deals", "type": "rss"},
        {"scraper": MySmartPriceSalesScraper, "type": "scrape"},
        {"scraper": AmazonSalesScraper, "type": "scrape"},
        {"scraper": FlipkartSalesScraper, "type": "scrape"},
    ],
    "US": [
        {"scraper": AmazonComSalesScraper, "type": "scrape"},
        {"scraper": CnetSalesScraper, "type": "scrape"},
        {"scraper": BestBuySalesScraper, "type": "scrape"}, 
    ],
    "GB": [
        {"scraper": TechRadarSalesScraper, "type": "scrape"},
    ],
    "AU": [
        {"scraper": FinderAUSalesScraper, "type": "scrape"},
        {"scraper": GadgetGuyAUSalesScraper, "type": "scrape"},
    ],
    "EU": [
        {"scraper": LesNumeriquesSalesScraper, "type": "scrape"},
        {"scraper": HeiseSalesScraper, "type": "scrape"},
        {"scraper": ChipDESalesScraper, "type": "scrape"},
    ],
    "JP": [
        {"scraper": AsciiJPSalesScraper, "type": "scrape"},
        {"scraper": ImpressWatchSalesScraper, "type": "scrape"},
    ],
    "CN": [
        {"scraper": ITHomeSalesScraper, "type": "scrape"},
        {"scraper": KuaiKeJiSalesScraper, "type": "scrape"},
    ]
}


# --- Scraping Functions ---
def scrape_from_rss(feed_url, region):
    print(f"Scraping RSS Feed: {feed_url}")
    try:
        feed_data = feedparser.parse(feed_url, agent=REQUEST_HEADERS.get('User-Agent'))

        if feed_data.bozo:
             print(f"  -> Warning: Feed parsing issue for {feed_url}. Error: {feed_data.bozo_exception}")

        print(f"  -> Found {len(feed_data.entries)} entries.")
        for entry in feed_data.entries:
            title = entry.get("title", "No Title").strip()
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            
            soup_summary = BeautifulSoup(summary, "html.parser")
            clean_summary = soup_summary.get_text(separator=' ', strip=True)
            text_content = title + " " + clean_summary

            keywords = ["sale", "festival", "deal", "offer", "discount", "days", "promo", "save"]
            if any(keyword in text_content.lower() for keyword in keywords):
                start_date, end_date = extract_dates(text_content)
                source_domain = urlparse(link).netloc.replace('www.','') if link else "unknown.com"
                platform = get_platform_from_title(title) or source_domain 

                sale = {
                    "title": title,
                    "description": clean_summary[:500],
                    "discount_percentage": None,
                    "source_domain": platform,
                    "region": region,
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                post_sale_to_api(sale)
    except Exception as e:
        print(f"  -> Error scraping RSS feed {feed_url}: {e}")


# --- Main Discovery Function ---
def discover_all_sales():
    print("--- Starting Curated Sales Discovery Task ---")
    PROCESSED_SALES_CACHE.clear()
    
    # Iterate over all defined regions and their sources
    for region, sources in CURATED_SOURCES.items():
        print(f"Processing region: {region}")
        for source in sources:
            if source["type"] == "rss":
                scrape_from_rss(source["url"], region)
            
            elif source["type"] == "scrape":
                try:
                    scraper_class = source["scraper"]
                    # Pass the USER_AGENT from this file to the scraper instance
                    scraper_instance = scraper_class(user_agent=USER_AGENT)
                    sales_list = scraper_instance.scrape()
                    print(f"  -> Modular scraper {scraper_class.__name__} found {len(sales_list)} sales.")
                    for sale in sales_list:
                        # Ensure the scraper's region is set, otherwise default
                        if "region" not in sale:
                            sale["region"] = region
                        post_sale_to_api(sale)
                except Exception as e:
                    print(f"  -> Error running modular scraper {source.get('scraper')}: {e}\n{traceback.format_exc()}")
            else:
                print(f"  -> Unknown source type: {source['type']} for {source.get('url')}")
                
    print(f"--- Finished Sales Discovery Task. Processed {len(PROCESSED_SALES_CACHE)} unique sales this run. ---")

# --- Direct execution for testing ---
if __name__ == '__main__':
    print("Running sales discovery directly for testing...")
    # You might need to adjust the SALES_API_URL for local testing
    # SALES_API_URL = "http://localhost:8000/api/sales/"
    discover_all_sales()
    print("Test run complete.")