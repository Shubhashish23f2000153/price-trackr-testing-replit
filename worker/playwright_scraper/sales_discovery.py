import requests
import feedparser
from bs4 import BeautifulSoup
import dateparser
from urllib.parse import urlparse
import json
from datetime import datetime, timezone, timedelta
import re
# --- 1. IMPORT PLAYWRIGHT ---
from playwright.sync_api import sync_playwright

# --- Configuration ---
SALES_API_URL = "http://backend:8000/api/sales/"
CURATED_SOURCES = {
    "IN": [
        {"url": "https://www.gadgets360.com/rss/news", "type": "rss"},
        {"url": "https://www.91mobiles.com/feed", "type": "rss"},
        {"url": "https://www.mysmartprice.com/deals/", "type": "scrape"},
        {"url": "https://timesofindia.indiatimes.com/rssfeeds/58867912.cms", "type": "rss"},
    ]
}
PROCESSED_SALES_CACHE = set()

# --- 2. USE THE SAME USER AGENT AS OUR OTHER SCRAPERS ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/'
}


# --- Helper Functions (Unchanged) ---
def normalize_string(s):
    return ' '.join(s.lower().split()) if s else ""

def extract_dates(text):
    start_date, end_date = None, None
    if not text: return start_date, end_date
    try:
        # Improved regex to find date ranges
        range_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})\s*to\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})', text, re.IGNORECASE)
        if range_match:
            start_str = f"{range_match.group(1)} {range_match.group(2)}"
            end_str = f"{range_match.group(3)} {range_match.group(4)}"
            start_date = dateparser.parse(start_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            end_date = dateparser.parse(end_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            return start_date, end_date

        date_matches = dateparser.search.search_dates(text, languages=['en'])
        if date_matches:
            date_matches.sort(key=lambda x: text.find(x[0]))
            
            now = datetime.now(timezone.utc)
            
            valid_dates = [d[1].replace(tzinfo=timezone.utc) if d[1].tzinfo is None else d[1] for d in date_matches if (d[1].replace(tzinfo=timezone.utc) if d[1].tzinfo is None else d[1]) > (now - timedelta(days=60))]

            if valid_dates:
                start_date = min(valid_dates) 
                if len(valid_dates) > 1:
                    potential_end = max(valid_dates)
                    if potential_end > start_date:
                        end_date = potential_end

                start_date = start_date.isoformat() if start_date else None
                end_date = end_date.isoformat() if end_date else None
                
    except Exception as e:
        print(f"Error parsing dates from text: '{text[:50]}...' - {e}")
    return start_date, end_date


def get_platform_from_title(title):
    title_lower = normalize_string(title)
    if not title_lower: return None
    if "amazon" in title_lower or "great indian festival" in title_lower:
        return "amazon.in"
    if "flipkart" in title_lower or "big billion days" in title_lower:
        return "flipkart.com"
    if "myntra" in title_lower:
        return "myntra.com"
    if "snapdeal" in title_lower:
        return "snapdeal.com"
    if "meesho" in title_lower:
        return "meesho.com"
    return None

def post_sale_to_api(sale_data: dict):
    if not sale_data.get("title") or not sale_data.get("source_domain"):
        return

    sale_title_norm = normalize_string(sale_data["title"])
    platform = sale_data["source_domain"]
    cache_key = (sale_title_norm, platform)

    if cache_key in PROCESSED_SALES_CACHE:
        return

    if sale_data.get("description"):
         sale_data["description"] = ' '.join(sale_data["description"].split())[:500] 

    print(f"Attempting to add sale: '{sale_title_norm}' from {platform}")
    try:
        start_dt, end_dt = None, None
        if sale_data.get("start_date"):
            try: start_dt = datetime.fromisoformat(sale_data["start_date"].replace('Z', '+00:00'))
            except: print(f"  -> Warning: Invalid start_date format: {sale_data.get('start_date')}")
        if sale_data.get("end_date"):
             try: end_dt = datetime.fromisoformat(sale_data["end_date"].replace('Z', '+00:00'))
             except: print(f"  -> Warning: Invalid end_date format: {sale_data.get('end_date')}")

        if start_dt and end_dt and end_dt <= start_dt:
            print(f"  -> Warning: Invalid date range for '{sale_title_norm}'. End date is before start date. Fixing end date.")
            sale_data["end_date"] = None 

        response = requests.post(SALES_API_URL, json=sale_data, timeout=10)
        response.raise_for_status()

        print(f"  -> Successfully posted sale: '{sale_title_norm}'")
        PROCESSED_SALES_CACHE.add(cache_key)

    except requests.exceptions.Timeout:
         print(f"  -> Failed to post sale: Timeout connecting to API at {SALES_API_URL}")
    except requests.exceptions.RequestException as e:
        error_msg = e.response.text if e.response else 'No response'
        status_code = e.response.status_code if e.response else 'N/A'
        if "duplicate key value violates unique constraint" in error_msg:
             print(f"  -> Info: Sale likely already exists (DB constraint).")
             PROCESSED_SALES_CACHE.add(cache_key) 
        else:
             print(f"  -> Failed to post sale (Status {status_code}): {error_msg}")
    except Exception as e:
        print(f"  -> Unexpected error processing or posting sale '{sale_title_norm}': {e}")

# --- Scraping Functions ---
def scrape_from_rss(feed_url, region):
    print(f"Scraping RSS Feed: {feed_url}")
    try:
        # Use the good user agent for RSS too
        feed_data = feedparser.parse(feed_url, agent=REQUEST_HEADERS.get('User-Agent'))

        if feed_data.bozo:
             # These errors are from the source, not us.
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

# --- 3. THIS FUNCTION IS NOW REWRITTEN ---
def scrape_from_html(page_url, region):
    """Scrapes MySmartPrice Deals page using Playwright."""
    print(f"Scraping HTML Page: {page_url}")
    if "mysmartprice.com" not in page_url:
        print(f"  -> Skipping HTML scrape for non-MySmartPrice URL: {page_url}")
        return
    
    html_content = ""
    try:
        # Use Playwright to launch a real browser
        with sync_playwright() as p:
            print(f"  -> Launching Playwright browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            
            # Go to the page
            page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
            
            # Get the HTML content
            html_content = page.content()
            browser.close()
            print(f"  -> Successfully fetched page with Playwright.")

        # Now, parse the content with BeautifulSoup (same as before)
        soup = BeautifulSoup(html_content, "lxml")
        
        deal_cards = soup.select('div[class^="msps-deals-card__"]')
        print(f"  -> Found {len(deal_cards)} potential MySmartPrice deal cards.")

        for card in deal_cards:
            title_element = card.select_one('a.msps-deals-card__title')
            description_element = card.select_one('.msps-deals-card__offertxt')
            store_element = card.select_one('.msps-deals-card__store > img') 

            title = title_element.get_text(strip=True) if title_element else "Unknown Sale"
            description = description_element.get_text(strip=True) if description_element else ""
            
            platform_name = ""
            if store_element and store_element.get('alt'):
                 platform_name = store_element['alt'].lower().replace(" logo","").strip()
                 if platform_name in ["amazon", "flipkart", "myntra", "meesho", "snapdeal"]:
                     platform_name += ".in" # Make it a valid domain
                 else:
                     platform_name += ".com" # Default
            
            if not platform_name or "unknown" in platform_name:
                 platform_name = get_platform_from_title(title) or "unknown.com"

            card_text = title + " " + description
            start_date, end_date = extract_dates(card_text)

            discount = None
            if description:
                 match = re.search(r'(\d+)% off', description, re.IGNORECASE)
                 if match:
                     try: discount = float(match.group(1))
                     except: pass

            sale = {
                "title": title,
                "description": description,
                "discount_percentage": discount,
                "source_domain": platform_name,
                "region": region,
                "start_date": start_date,
                "end_date": end_date,
                "is_active": True
            }
            post_sale_to_api(sale)
            
    except Exception as e:
        print(f"  -> Error scraping HTML page {page_url} with Playwright: {e}")

# --- Main Discovery Function ---
def discover_all_sales():
    print("--- Starting Curated Sales Discovery Task ---")
    PROCESSED_SALES_CACHE.clear()
    for region, sources in CURATED_SOURCES.items():
        print(f"Processing region: {region}")
        for source in sources:
            if source["type"] == "rss":
                scrape_from_rss(source["url"], region)
            elif source["type"] == "scrape":
                scrape_from_html(source["url"], region)
            else:
                print(f"  -> Unknown source type: {source['type']} for {source['url']}")
    print(f"--- Finished Sales Discovery Task. Processed {len(PROCESSED_SALES_CACHE)} unique sales this run. ---")

# --- Direct execution for testing ---
if __name__ == '__main__':
    print("Running sales discovery directly for testing...")
    discover_all_sales()
    print("Test run complete.")