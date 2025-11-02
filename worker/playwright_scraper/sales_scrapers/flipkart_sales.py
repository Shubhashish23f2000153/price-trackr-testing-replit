from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_helpers import extract_dates, get_platform_from_title, post_sale_to_api

class FlipkartSalesScraper(BaseSalesScraper):
    """Scrapes Flipkart's main 'Offers' page for sales."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        # This is Flipkart's main "Top Offers" page
        self.url = "https://www.flipkart.com/offers-list"

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
                
                # Wait for the main offer container to be present
                page.wait_for_selector('div[class*="_1-T_j2"]', timeout=15000)
                
                # Scroll a bit to load any dynamic content
                page.evaluate("window.scrollTo(0, 1500)")
                page.wait_for_timeout(1000)

                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # Find all deal "cards"
            # Selector for the main offer cards on the page
            deal_cards = soup.select('a[class*="_1-T_j2"]')
            
            print(f"  -> Found {len(deal_cards)} potential Flipkart deal cards.")

            for card in deal_cards:
                # Title is usually in a <p> tag
                title_element = card.select_one('p[class*="_1-t_O_"]')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue # Skip if there's no title

                # Description / discount is in another <p>
                discount = None
                description_text = ""
                description_element = card.select_one('p[class*="_3_r0sI"]')
                if description_element:
                    description_text = description_element.get_text(strip=True)
                    # Look for formats like "Up to 70% Off" or "Min. 50% Off"
                    match = re.search(r'(\d+)% Off', description_text, re.IGNORECASE)
                    if match:
                        try: 
                            discount = float(match.group(1))
                        except: 
                            pass

                # Dates are not available on these cards
                start_date, end_date = None, None

                sale = {
                    "title": title,
                    "description": description_text, # Use the discount text as description
                    "discount_percentage": discount,
                    "source_domain": "flipkart.com",
                    "region": "IN",
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found