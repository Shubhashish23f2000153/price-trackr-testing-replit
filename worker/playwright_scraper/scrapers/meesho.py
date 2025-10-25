from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict

class MeeshoScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        title_selectors = ['h1']
        # ... (title logic) ...
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text(timeout=5000).strip()
                if title: break
            except: continue
        if not title: title = "Unknown Product"

        price_text = ""
        # --- REORDERED PRICE SELECTORS ---
        price_selectors = [
            'h4', # Generic first
            'h4.sc-eDV5Ve',
            'h4[class*="Price__PriceValue"]'
        ]
        # ... (price extraction logic) ...
        for selector in price_selectors:
            try:
                full_price_text = page.locator(selector).first.inner_text(timeout=5000).strip()
                import re
                price_match = re.search(r'₹?([\d,]+)', full_price_text)
                if price_match and price_match.group(1):
                    price_text = price_match.group(1)
                    break
            except: continue


        image_url = ""
        # ... (image logic) ...
        image_selectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img']
        for selector in image_selectors:
            try:
                img_element = page.locator(selector).first
                src = img_element.get_attribute('src', timeout=5000)
                if src and src.startswith('http'):
                    image_url = src
                    break
            except: continue


        description = ""
        # ... (description logic) ...
        description_selectors = ['div[class*="ProductDescription__DescriptionContainer"]', 'div.content']
        for selector in description_selectors:
            try:
                desc_element = page.locator(selector).first
                description = desc_element.inner_text(timeout=5000).strip()
                if description: break
            except: continue


        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        # ... (title logic) ...
        title = None
        title_selectors = ['h1']
        for selector in title_selectors:
             title = soup.select_one(selector)
             if title: break
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = None
        price_text_raw = ""
        # --- REORDERED PRICE SELECTORS ---
        price_selectors = [
            'h4', # Generic first
            'h4.sc-eDV5Ve',
            'h4[class*="Price__PriceValue"]'
        ]
        # ... (price extraction logic) ...
        for selector in price_selectors:
             price = soup.select_one(selector)
             if price:
                 price_text_raw = price.get_text().strip()
                 break
        price_text = "0"
        import re
        if price_text_raw:
            price_match = re.search(r'₹?([\d,]+)', price_text_raw)
            if price_match and price_match.group(1):
                price_text = price_match.group(1)


        # ... (image logic) ...
        image = None
        image_selectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                 src = image.get('src')
                 if src and src.startswith('http'): break
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""


        # ... (description logic) ...
        description = None
        description_selectors = ['div[class*="ProductDescription__DescriptionContainer"]', 'div.content']
        for selector in description_selectors:
            description = soup.select_one(selector)
            if description and description.get_text().strip(): break
        description_text = description.get_text().strip() if description else ""


        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text
        }