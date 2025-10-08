from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, Optional


class BaseScraper(ABC):
    def __init__(self, url: str):
        self.url = url
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    @abstractmethod
    def extract_data(self, page: Page) -> Dict:
        """Extract product data from the page"""
        pass
    
    @abstractmethod
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction using BeautifulSoup"""
        pass
    
    def scrape(self) -> Optional[Dict]:
        """Main scraping method with Playwright"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                # Random delay before request
                time.sleep(random.uniform(1, 3))
                
                page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # Extract data
                data = self.extract_data(page)
                
                browser.close()
                return data
                
        except Exception as e:
            print(f"Playwright scraping failed: {e}")
            return self.scrape_fallback()
    
    def scrape_fallback(self) -> Optional[Dict]:
        """Fallback scraping with requests + BeautifulSoup"""
        try:
            import requests
            headers = {'User-Agent': self.user_agent}
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return self.extract_data_fallback(response.text)
            
        except Exception as e:
            print(f"Fallback scraping failed: {e}")
            return None
    
    @staticmethod
    def normalize_price(price_str: str) -> int:
        """Convert price string to cents/paise"""
        import re
        # Remove currency symbols and commas
        price_str = re.sub(r'[₹$,\s]', '', price_str)
        # Extract numeric value
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100)
        return 0
