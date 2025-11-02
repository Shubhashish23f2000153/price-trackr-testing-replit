from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_discovery import extract_dates, post_sale_to_api

class AmazonSalesScraper(BaseSalesScraper):
    """Scrapes Amazon.in's main 'Today's Deals' page for sales."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.amazon.in/deals"

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                
                print(f"  -> Navigating to {self.url}")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                
                # Scroll to load 'infinite scroll' deals
                for _ in range(3): # Scroll 3 times
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1500) # Wait for content to load

                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched and scrolled page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # Find all deal "widgets" or "cards"
            # Selectors based on Amazon's typical deals page structure
            deal_cards = soup.select('div[class*="DealGridItem"]')
            
            print(f"  -> Found {len(deal_cards)} potential Amazon deal cards.")

            for card in deal_cards:
                title_element = card.select_one('div[class*="DealTitle"]')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue # Skip if there's no title

                # Try to find discount percentage
                discount = None
                discount_element = card.select_one('div[class*="DealPrice"]')
                if discount_element:
                    discount_text = discount_element.get_text(strip=True)
                    # Look for formats like "Up to 70% off" or "50% off"
                    match = re.search(r'(\d+)% off', discount_text, re.IGNORECASE)
                    if match:
                        try: 
                            discount = float(match.group(1))
                        except: 
                            pass

                # Dates are rarely listed on these cards, so we leave them None
                start_date, end_date = None, None

                sale = {
                    "title": title,
                    "description": f"Deal on {title}", # Amazon rarely provides descriptions here
                    "discount_percentage": discount,
                    "source_domain": "amazon.in",
                    "region": "IN",
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found