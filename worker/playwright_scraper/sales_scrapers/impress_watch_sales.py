from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_discovery import extract_dates, get_platform_from_title

class ImpressWatchSalesScraper(BaseSalesScraper):
    """Scrapes Impress Watch's 'Sale' section for deals."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.watch.impress.co.jp/docs/news/sale/" # JP Sale page

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Set locale to ja-JP
                context = browser.new_context(user_agent=self.user_agent, locale="ja-JP")
                page = context.new_page()
                
                print(f"  -> Navigating to {self.url}")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                # Wait for the main list of articles
                page.wait_for_selector('li.item', timeout=10000)
                
                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # Select all article list items
            deal_articles = soup.select('li.item')
            
            print(f"  -> Found {len(deal_articles)} potential Impress Watch deal articles.")

            for article in deal_articles:
                title_element = article.select_one('h3.title')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue

                description_element = article.select_one('p.summary')
                description = description_element.get_text(strip=True) if description_element else f"Deal on {title}"

                # Check for Japanese keywords (sale, discount, bargain, price) + English
                keywords = ["セール", "割引", "お得", "価格", "オファー", "deal", "sale", "キャンペーン"] # Added "campaign"
                text_content = title + " " + description
                if not any(keyword in text_content.lower() for keyword in keywords):
                    continue

                discount = None
                match = re.search(r'(\d+)%', text_content) # Look for %
                if match:
                    try: 
                        discount = float(match.group(1))
                    except: 
                        pass

                start_date, end_date = extract_dates(text_content)
                
                # Determine platform from title (e.g., "Amazon", "Rakuten")
                platform = get_platform_from_title(title) or "unknown.com"

                sale = {
                    "title": title,
                    "description": description,
                    "discount_percentage": discount,
                    "source_domain": platform,
                    "region": "JP", # Japan
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found