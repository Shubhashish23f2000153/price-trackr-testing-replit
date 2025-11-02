from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from .base_sales_scraper import BaseSalesScraper
from ..sales_helpers import extract_dates, get_platform_from_title, post_sale_to_api

class KuaiKeJiSalesScraper(BaseSalesScraper):
    """Scrapes KuaiKeJi.com's 'Deals' (快查) section for sales."""
    
    def __init__(self, user_agent: str):
        super().__init__(user_agent)
        self.url = "https://www.kuaikeji.com/list/kc.html" # CN Deals page

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"Scraping HTML Page: {self.url}")
        
        sales_found = []
        html_content = ""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Set locale to zh-CN
                context = browser.new_context(user_agent=self.user_agent, locale="zh-CN")
                page = context.new_page()
                
                print(f"  -> Navigating to {self.url}")
                page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                # Wait for the main list of articles
                page.wait_for_selector('div.list_wrap ul li', timeout=10000)
                
                html_content = page.content()
                browser.close()
                print(f"  -> Successfully fetched page.")

            soup = BeautifulSoup(html_content, "lxml")
            
            # Select all article list items
            deal_articles = soup.select('div.list_wrap ul li')
            
            print(f"  -> Found {len(deal_articles)} potential KuaiKeJi.com articles.")

            for article in deal_articles:
                title_element = article.select_one('h2 a')
                title = title_element.get_text(strip=True) if title_element else None
                
                if not title:
                    continue

                description_element = article.select_one('div.intro') # Synopsis
                description = description_element.get_text(strip=True) if description_element else f"Deal on {title}"

                # Check for Chinese keywords (discount, promotion, special price, price)
                keywords = ["优惠", "促销", "打折", "特价", "价格", "deal", "sale", "快查"]
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
                
                # Determine platform from title (e.g., "京东" - JD, "天猫" - Tmall)
                platform = get_platform_from_title(title) or "unknown.com"
                if "京东" in title:
                    platform = "jd.com"
                elif "天猫" in title:
                    platform = "tmall.com"

                sale = {
                    "title": title,
                    "description": description,
                    "discount_percentage": discount,
                    "source_domain": platform,
                    "region": "CN", # China
                    "start_date": start_date,
                    "end_date": end_date,
                    "is_active": True
                }
                sales_found.append(sale)
                
        except Exception as e:
            print(f"  -> Error scraping HTML page {self.url} with Playwright: {e}")
            
        return sales_found