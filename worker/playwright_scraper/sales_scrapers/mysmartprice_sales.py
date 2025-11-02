from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_discovery import extract_dates, get_platform_from_title, post_sale_to_api

class MySmartPriceSalesScraper(BaseSalesScraper):
    """Scrapes MySmartPrice Deals page using Playwright."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.mysmartprice.com/deals/"

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                
                page.wait_for_timeout(2000)
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(1000)

                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page with Playwright.")

            soup = BeautifulSoup(html_content, "lxml")
            
            deal_cards = soup.select('div.deals-card-item')
            if not deal_cards:
                 deal_cards = soup.select('div[class^="msps-deals-card__"]')
            
            print(f"  -> Found {len(deal_cards)} potential MySmartPrice deal cards.")

            for card in deal_cards:
                title_element = card.select_one('a.deals-card-item__title')
                description_element = card.select_one('div.deals-card-item__offer, .msps-deals-card__offertxt')
                store_element = card.select_one('img.deals-card-item__store-logo, .msps-deals-card__store > img') 

                title = title_element.get_text(strip=True) if title_element else "Unknown Sale"
                description = description_element.get_text(strip=True) if description_element else ""
                
                platform_name = ""
                if store_element and store_element.get('alt'):
                     platform_name = store_element['alt'].lower().replace(" logo","").strip()
                     if platform_name in ["amazon", "flipkart", "myntra", "meesho", "snapdeal"]:
                         platform_name += ".in"
                     else:
                         platform_name += ".com"
                
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
                    "region": "IN", # Hardcoded for this scraper
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found