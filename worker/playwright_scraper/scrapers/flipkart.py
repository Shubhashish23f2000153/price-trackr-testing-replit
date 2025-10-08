from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict


class FlipkartScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        try:
            title_elem = page.locator('.B_NuCI, .VU-ZEz').first
            title = title_elem.inner_text().strip()
        except:
            title = "Unknown Product"
        
        price_text = ""
        try:
            price_elem = page.locator('._30jeq3, ._1vC4OE').first
            price_text = price_elem.inner_text()
        except:
            pass
        
        availability = "In Stock"
        try:
            avail_elem = page.locator('._16FRp0').first
            if avail_elem:
                availability = avail_elem.inner_text().strip()
        except:
            pass
        
        image_url = ""
        try:
            image_elem = page.locator('._396cs4').first
            if image_elem:
                image_url = image_elem.get_attribute('src')
        except:
            pass
        
        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "stock" in availability.lower() or "available" in availability.lower(),
            "url": self.url,
            "image_url": image_url
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')
        
        title = soup.select_one('.B_NuCI, .VU-ZEz')
        title_text = title.get_text().strip() if title else "Unknown Product"
        
        price = soup.select_one('._30jeq3, ._1vC4OE')
        price_text = price.get_text() if price else "0"
        
        availability = soup.select_one('._16FRp0')
        avail_text = availability.get_text().strip() if availability else "In Stock"
        
        image = soup.select_one('._396cs4')
        image_url = image.get('src', '') if image else ""
        
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url
        }
