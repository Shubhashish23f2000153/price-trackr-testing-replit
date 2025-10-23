# 1. Added missing imports
from playwright.sync_api import Page
from bs4 import BeautifulSoup
from typing import Dict 
# --------------------
from ..base_scraper import BaseScraper

class FlipkartScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        title_selectors = ['span.VU-ZEz', 'span.B_NuCI']
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text().strip()
                if title:
                    break 
            except:
                continue
        if not title:
             title = "Unknown Product"
        
        price_text = ""
        price_selectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child']
        for selector in price_selectors:
            try:
                price_text = page.locator(selector).first.inner_text()
                if price_text:
                    break 
            except:
                continue
        
        availability = "In Stock"
        try:
            avail_elem = page.locator('._16FRp0').first 
            if avail_elem:
                availability = avail_elem.inner_text().strip()
        except:
            pass
        
        image_url = ""
        image_selectors = ['img._396cs4', 'img._2r_T1E']
        for selector in image_selectors:
            try:
                image_url = page.locator(selector).first.get_attribute('src')
                if image_url:
                    break 
            except:
                continue
        
        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "stock" in availability.lower() or "available" in availability.lower(),
            "url": self.url,
            "image_url": image_url
        }
    
    # 2. Corrected indentation for this method definition
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')
        
        title = None
        title_selectors = ['span.VU-ZEz', 'span.B_NuCI']
        for selector in title_selectors:
            title = soup.select_one(selector)
            if title:
                break
        title_text = title.get_text().strip() if title else "Unknown Product"
        
        price = None
        price_selectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child']
        for selector in price_selectors:
            price = soup.select_one(selector)
            if price:
                break
        price_text = price.get_text() if price else "0"
        
        availability = soup.select_one('._16FRp0')
        avail_text = availability.get_text().strip() if availability else "In Stock"
        
        image = None
        image_selectors = ['img._396cs4', 'img._2r_T1E']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                break
        image_url = image.get('src', '') if image else ""
        
        return {
            "title": title_text,
            # 3. Corrected variable name from priceText to price_text
            "price": self.normalize_price(price_text), 
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url
        }