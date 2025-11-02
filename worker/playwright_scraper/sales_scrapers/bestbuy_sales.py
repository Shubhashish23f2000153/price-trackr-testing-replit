from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_helpers import extract_dates, get_platform_from_title, post_sale_to_api

class BestBuySalesScraper(BaseSalesScraper):
    """Scrapes BestBuy.com's 'Deals' section for sales."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.bestbuy.com/deals" # US Deals page

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Set locale to en-US
                context = browser.new_context(user_agent=self.user_agent, locale="en-US")
                page = context.new_page()
                
                print(f"  -> Navigating to {self.url}")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                # Wait for the main deals container
                page.wait_for_selector('div.deals-container', timeout=15000)
                
                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # Select both "Sale Event" cards (like Black Friday) and individual "Deal" cards
            deal_cards = soup.select('div[class*="sale-event-card"], div[class*="deal-card"]')
            
            print(f"  -> Found {len(deal_cards)} potential BestBuy deal articles.")

            for card in deal_cards:
                title_element = card.select_one('h3') # General h3 title
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue

                description_element = card.select_one('p[class*="sale-event-card__callout"], p[class*="deal-card__description"]')
                description = description_element.get_text(strip=True) if description_element else f"Deal on {title}"

                # Big sale cards often have explicit dates
                date_element = card.select_one('div[class*="sale-event-card__dates"]')
                date_text = date_element.get_text(strip=True) if date_element else ""

                # Combine all text to check for keywords and dates
                text_content = title + " " + description + " " + date_text

                # Check for keywords
                keywords = ["deal", "discount", "save", "offer", "sale", "price drop", "black friday"]
                if not any(keyword in text_content.lower() for keyword in keywords):
                    continue

                discount = None
                match = re.search(r'(\d+)% off', text_content, re.IGNORECASE)
                if match:
                    try: 
                        discount = float(match.group(1))
                    except: 
                        pass

                start_date, end_date = extract_dates(text_content)
                
                sale = {
                    "title": title,
                    "description": description,
                    "discount_percentage": discount,
                    "source_domain": "bestbuy.com",
                    "region": "US", # US Scraper
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found