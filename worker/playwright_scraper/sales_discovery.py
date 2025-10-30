import requests
import feedparser
from bs4 import BeautifulSoup
import dateparser
from urllib.parse import urlparse
import json
from datetime import datetime, timezone, timedelta
import re # <-- ADD THIS LINE

# --- Configuration ---
SALES_API_URL = "http://backend:8000/api/sales/"
CURATED_SOURCES = {
    "IN": [
        {"url": "https://www.gadgets360.com/rss/news", "type": "rss"},
        {"url": "https://www.91mobiles.com/feed", "type": "rss"},
        {"url": "https://www.mysmartprice.com/deals/", "type": "scrape"},
        # Add Times of India Shopping for broader coverage
        {"url": "https://timesofindia.indiatimes.com/rssfeeds/58867912.cms", "type": "rss"},
    ]
}
PROCESSED_SALES_CACHE = set()

# --- Helper Functions (Mostly unchanged) ---
def normalize_string(s):
    return ' '.join(s.lower().split()) if s else ""

def extract_dates(text):
    start_date, end_date = None, None
    if not text: return start_date, end_date
    try:
        date_matches = dateparser.search.search_dates(text, languages=['en'])
        if date_matches:
            date_matches.sort(key=lambda x: text.find(x[0]))
            
            now = datetime.now(timezone.utc)
            
            # Filter out dates significantly in the past unless explicitly stated
            valid_dates = [d[1].replace(tzinfo=timezone.utc) if d[1].tzinfo is None else d[1] for d in date_matches if (d[1].replace(tzinfo=timezone.utc) if d[1].tzinfo is None else d[1]) > (now - timedelta(days=60))]

            if valid_dates:
                start_date = min(valid_dates) # Earliest relevant date is start
                if len(valid_dates) > 1:
                    potential_end = max(valid_dates)
                    # Simple check: end date should be after start date
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
    # Basic validation
    if not sale_data.get("title") or not sale_data.get("source_domain"):
        # print("Skipping incomplete sale data.")
        return

    # Normalize title for caching
    sale_title_norm = normalize_string(sale_data["title"])
    platform = sale_data["source_domain"]
    cache_key = (sale_title_norm, platform)

    if cache_key in PROCESSED_SALES_CACHE:
        # print(f"Skipping duplicate sale (in this run): {sale_title_norm}")
        return

    # Clean description (optional, but good practice)
    if sale_data.get("description"):
         sale_data["description"] = ' '.join(sale_data["description"].split())[:500] # Limit length

    print(f"Attempting to add sale: '{sale_title_norm}' from {platform}")
    try:
        # Check date validity
        start_dt, end_dt = None, None
        if sale_data.get("start_date"):
            try: start_dt = datetime.fromisoformat(sale_data["start_date"].replace('Z', '+00:00'))
            except: print(f"  -> Warning: Invalid start_date format: {sale_data.get('start_date')}")
        if sale_data.get("end_date"):
             try: end_dt = datetime.fromisoformat(sale_data["end_date"].replace('Z', '+00:00'))
             except: print(f"  -> Warning: Invalid end_date format: {sale_data.get('end_date')}")

        if start_dt and end_dt and end_dt <= start_dt:
            print(f"  -> Warning: Invalid date range for '{sale_title_norm}'. End date is before start date. Fixing end date.")
            sale_data["end_date"] = None # Remove invalid end date

        # TODO: Add API check for existing sale before POSTing
        # response_check = requests.get(SALES_API_URL, params={"title": sale_title_norm, ...})

        response = requests.post(SALES_API_URL, json=sale_data, timeout=10)
        response.raise_for_status()

        print(f"  -> Successfully posted sale: '{sale_title_norm}'")
        PROCESSED_SALES_CACHE.add(cache_key)

    except requests.exceptions.Timeout:
         print(f"  -> Failed to post sale: Timeout connecting to API at {SALES_API_URL}")
    except requests.exceptions.RequestException as e:
        error_msg = e.response.text if e.response else 'No response'
        status_code = e.response.status_code if e.response else 'N/A'
        # Avoid logging full duplicate errors if API returns specific message
        if "duplicate key value violates unique constraint" in error_msg:
             print(f"  -> Info: Sale likely already exists (DB constraint).")
             PROCESSED_SALES_CACHE.add(cache_key) # Add to cache so we don't retry
        else:
             print(f"  -> Failed to post sale (Status {status_code}): {error_msg}")
    except Exception as e:
        print(f"  -> Unexpected error processing or posting sale '{sale_title_norm}': {e}")

# --- Scraping Functions ---
def scrape_from_rss(feed_url, region):
    print(f"Scraping RSS Feed: {feed_url}")
    try:
        # Added User-Agent to potentially avoid blocks
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        feed_data = feedparser.parse(feed_url, agent=headers.get('User-Agent'))

        if feed_data.bozo:
             print(f"  -> Warning: Feed parsing issue for {feed_url}. Error: {feed_data.bozo_exception}")

        print(f"  -> Found {len(feed_data.entries)} entries.")
        for entry in feed_data.entries:
            title = entry.get("title", "No Title").strip()
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            
            # Use BeautifulSoup to clean summary HTML
            soup_summary = BeautifulSoup(summary, "html.parser")
            clean_summary = soup_summary.get_text(separator=' ', strip=True)
            text_content = title + " " + clean_summary

            keywords = ["sale", "festival", "deal", "offer", "discount", "days", "promo", "save"]
            if any(keyword in text_content.lower() for keyword in keywords):
                start_date, end_date = extract_dates(text_content)
                source_domain = urlparse(link).netloc.replace('www.','') if link else "unknown.com"
                platform = get_platform_from_title(title) or source_domain # Prioritize inferred platform

                sale = {
                    "title": title,
                    "description": clean_summary[:500], # Limit length
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

def scrape_from_html(page_url, region):
    """Scrapes MySmartPrice Deals page."""
    print(f"Scraping HTML Page: {page_url}")
    if "mysmartprice.com" not in page_url:
        print(f"  -> Skipping HTML scrape for non-MySmartPrice URL: {page_url}")
        return
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(page_url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        # --- Selectors for MySmartPrice Deals ---
        # Find all deal cards. The structure seems to be divs with class starting 'msps-deals-card__'
        deal_cards = soup.select('div[class^="msps-deals-card__"]')
        print(f"  -> Found {len(deal_cards)} potential MySmartPrice deal cards.")

        for card in deal_cards:
            title_element = card.select_one('a.msps-deals-card__title') # Title is in a link
            description_element = card.select_one('.msps-deals-card__offertxt') # Offer text often has details
            store_element = card.select_one('.msps-deals-card__store > img') # Store logo in an img tag

            title = title_element.get_text(strip=True) if title_element else "Unknown Sale"
            description = description_element.get_text(strip=True) if description_element else ""
            
            # Platform name often in the img alt text or derivable from title
            platform_name = ""
            if store_element and store_element.get('alt'):
                 platform_name = store_element['alt'].lower().replace(" logo","").strip() + ".com" # e.g. "amazon logo" -> amazon.com
            if not platform_name:
                 platform_name = get_platform_from_title(title) or "unknown.com" # Fallback

            # Combine title and description for date parsing
            card_text = title + " " + description
            start_date, end_date = extract_dates(card_text)

            # Try to extract discount percentage if available (often in offer text)
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
                "source_domain": platform_name, # Use detected platform
                "region": region,
                "start_date": start_date,
                "end_date": end_date,
                "is_active": True
            }
            post_sale_to_api(sale)
            
    except requests.exceptions.RequestException as e:
        print(f"  -> Error fetching HTML page {page_url}: {e}")
    except Exception as e:
        print(f"  -> Error scraping HTML page {page_url}: {e}")

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
    # Add DATABASE_URL to environment if running directly and worker needs it (it doesn't currently)
    # import os
    # os.environ['DATABASE_URL'] = 'postgresql://pricetrackr:testpassword@localhost:5432/pricetrackr'
    discover_all_sales()
    print("Test run complete.")