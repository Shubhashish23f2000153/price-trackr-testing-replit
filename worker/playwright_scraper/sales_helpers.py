import requests
import feedparser
from bs4 import BeautifulSoup
import dateparser
from urllib.parse import urlparse
import json
from datetime import datetime, timezone, timedelta
import re

# --- Constants ---
SALES_API_URL = "http://backend:8000/api/sales/"
PROCESSED_SALES_CACHE = set()

# --- Helper Functions ---
def normalize_string(s):
    return ' '.join(s.lower().split()) if s else ""

def extract_dates(text):
    start_date, end_date = None, None
    if not text: return start_date, end_date
    try:
        # Look for "Month Day to Month Day" (e.g., Nov 25 to Nov 29)
        range_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})\s*(?:to|-|–)\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})', text, re.IGNORECASE)
        if range_match:
            start_str = f"{range_match.group(1)} {range_match.group(2)}"
            end_str = f"{range_match.group(3)} {range_match.group(4)}"
            start_date = dateparser.parse(start_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            end_date = dateparser.parse(end_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            return start_date, end_date
            
        # Look for "Month Day - Day" (e.g., Nov 25 - 29)
        range_match_short = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})', text, re.IGNORECASE)
        if range_match_short:
            month = range_match_short.group(1)
            start_str = f"{month} {range_match_short.group(2)}"
            end_str = f"{month} {range_match_short.group(3)}"
            start_date = dateparser.parse(start_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            end_date = dateparser.parse(end_str, settings={'PREFER_DATES_FROM': 'future'}).isoformat()
            return start_date, end_date

        # Fallback to finding any dates
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
    # Add more platform checks as needed
    if "amazon" in title_lower:
        return "amazon.com" # Default to .com, region will override
    if "flipkart" in title_lower or "big billion days" in title_lower:
        return "flipkart.com"
    if "best buy" in title_lower or "black friday" in title_lower:
        return "bestbuy.com"
    if "myntra" in title_lower:
        return "myntra.com"
    if "snapdeal" in title_lower:
        return "snapdeal.com"
    if "meesho" in title_lower:
        return "meesho.com"
    if "jd.com" in title_lower or "京东" in title_lower:
        return "jd.com"
    if "tmall" in title_lower or "天猫" in title_lower:
        return "tmall.com"
    if "rakuten" in title_lower or "楽天" in title_lower:
        return "rakuten.co.jp"
    if "media markt" in title_lower:
        return "mediamarkt.de"
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