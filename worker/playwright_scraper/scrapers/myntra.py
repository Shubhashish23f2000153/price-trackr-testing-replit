from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict

class MyntraScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        # --- !! TODO: Find the correct selectors !! ---
        TITLE_SELECTOR = '.pdp-title'
        PRICE_SELECTOR = '.pdp-price'
        IMAGE_SELECTOR = '.image-grid-image'
        # --- End of selectors ---

        title = "Unknown Product"
        try:
            title_elem = page.locator(TITLE_SELECTOR).first
            title = title_elem.inner_text().strip()
        except:
            pass # Keep default title

        price_text = ""
        try:
            price_elem = page.locator(PRICE_SELECTOR).first
            price_text = price_elem.inner_text()
        except:
            pass # Keep empty price

        image_url = ""
        try:
            image_elem = page.locator(IMAGE_SELECTOR).first
            if image_elem:
                # Myntra images are often in 'style' attributes
                style_attr = image_elem.get_attribute('style')
                if style_attr and 'url(' in style_attr:
                     image_url = style_attr.split('url("')[1].split('")')[0]
        except:
            pass

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock", # Myntra often hides this
            "in_stock": True,
            "url": self.url,
            "image_url": image_url
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        # This is a basic fallback, selectors will need refinement
        soup = BeautifulSoup(html, 'lxml')
        
        title = soup.select_one('.pdp-title')
        title_text = title.get_text().strip() if title else "Unknown Product"
        
        price = soup.select_one('.pdp-price')
        price_text = price.get_text() if price else "0"
        
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": "" # Fallback image is hard
        }