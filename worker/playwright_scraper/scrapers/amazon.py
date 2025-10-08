from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict


class AmazonScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = page.locator('#productTitle').inner_text().strip()
        
        # Try multiple price selectors
        price_elem = None
        price_selectors = [
            '.a-price-whole',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price .a-offscreen'
        ]
        
        price_text = ""
        for selector in price_selectors:
            try:
                price_elem = page.locator(selector).first
                if price_elem:
                    price_text = price_elem.inner_text()
                    break
            except:
                continue
        
        availability = "Unknown"
        try:
            avail_elem = page.locator('#availability span').first
            if avail_elem:
                availability = avail_elem.inner_text().strip()
        except:
            pass
        
        image_url = ""
        try:
            image_elem = page.locator('#landingImage').first
            if image_elem:
                image_url = image_elem.get_attribute('src')
        except:
            pass
        
        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "in stock" in availability.lower(),
            "url": self.url,
            "image_url": image_url
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')
        
        title = soup.select_one('#productTitle')
        title_text = title.get_text().strip() if title else "Unknown Product"
        
        price = soup.select_one('.a-price-whole, #priceblock_ourprice')
        price_text = price.get_text() if price else "0"
        
        availability = soup.select_one('#availability span')
        avail_text = availability.get_text().strip() if availability else "Unknown"
        
        image = soup.select_one('#landingImage')
        image_url = image.get('src', '') if image else ""
        
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "in stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url
        }
