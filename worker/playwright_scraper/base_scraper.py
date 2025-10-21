from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Page
import time
import random
from typing import Dict, Optional
import os

class BaseScraper(ABC):
    def __init__(self, url: str):
        self.url = url
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        
    @abstractmethod
    def extract_data(self, page: Page) -> Dict:
        pass
    
    @abstractmethod
    def extract_data_fallback(self, html: str) -> Dict:
        pass
    
    def scrape(self) -> Optional[Dict]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()
                
                time.sleep(random.uniform(2, 5))
                
                page.goto(self.url, wait_until='domcontentloaded', timeout=90000)
                
                page.evaluate("window.scrollBy(0, window.innerHeight);")
                time.sleep(random.uniform(1, 3))

                data = self.extract_data(page)
                
                browser.close()
                return data
                
        except Exception as e:
            print(f"Playwright scraping failed: {e}")
            return None
    
    # Fallback and normalize_price methods are no longer needed with the Scraping API model,
    # but we leave them in case you switch back from the hybrid model.
    def scrape_fallback(self, html: str) -> Optional[Dict]:
        return None
    
    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        price_str = re.sub(r'[₹$,\s]', '', price_str)
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100)
        return 0