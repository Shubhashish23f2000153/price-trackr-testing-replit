from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict

class SnapdealScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        # --- !! TODO: Find the correct selectors !! ---
        TITLE_SELECTOR = '.pdp-e-i-head'
        PRICE_SELECTOR = '.payBlkBig'
        IMAGE_SELECTOR = '#bx-slider-left-image-panel .cloudzoom'
        # --- End of selectors ---

        title = "Unknown Product"
        try:
            title_elem = page.locator(TITLE_SELECTOR).first
            title = title_elem.inner_text().strip()
        except:
            pass 

        price_text = ""
        try:
            price_elem = page.locator(PRICE_SELECTOR).first
            price_text = price_elem.inner_text()
        except:
            pass 

        image_url = ""
        try:
            image_elem = page.locator(IMAGE_SELECTOR).first
            if image_elem:
                image_url = image_elem.get_attribute('src')
        except:
            pass

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'lxml')
        title = soup.select_one('.pdp-e-i-head')
        title_text = title.get_text().strip() if title else "Unknown Product"
        price = soup.select_one('.payBlkBig')
        price_text = price.get_text() if price else "0"
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": ""
        }