from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_discovery import extract_dates, get_platform_from_title, post_sale_to_api

class CnetSalesScraper(BaseSalesScraper):
    """Scrapes CNET's 'Deals' section for sales."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.cnet.com/deals/"

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent, locale="en-US")
                page = context.new_page()
                
                print(f"  -> Navigating to {self.url}")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                page.wait_for_selector('div[class*="c-entryCard"]', timeout=10000)
                
                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # CNET uses "Entry Cards" for articles
            deal_cards = soup.select('div[class*="c-entryCard"]')
            
            print(f"  -> Found {len(deal_cards)} potential CNET deal articles.")

            for card in deal_cards:
                title_element = card.select_one('h3')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue

                description_element = card.select_one('p[class*="c-entryCard_dek"]')
                description = description_element.get_text(strip=True) if description_element else f"Deal on {title}"

                # Check for keywords to ensure it's a deal
                keywords = ["deal", "discount", "save", "offer", "sale", "price drop"]
                if not any(keyword in title.lower() or keyword in description.lower() for keyword in keywords):
                    continue # Skip if it's not clearly a deal article

                # Try to find discount percentage
                discount = None
                text_content = title + " " + description
                match = re.search(r'(\d+)% off', text_content, re.IGNORECASE)
                if match:
                    try: 
                        discount = float(match.group(1))
                    except: 
                        pass

                # Dates are often in the text
                start_date, end_date = extract_dates(text_content)
                
                # Determine platform from title
                platform = get_platform_from_title(title) or "unknown.com"

                sale = {
                    "title": title,
                    "description": description,
                    "discount_percentage": discount,
                    "source_domain": platform,
                    "region": "US",
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found