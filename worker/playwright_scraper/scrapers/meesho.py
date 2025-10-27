from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict
import re # Import regex

class MeeshoScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        title_selectors = ['h1']
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text(timeout=5000).strip()
                if title: break
            except: continue
        if not title: title = "Unknown Product"

        price_text = ""
        price_selectors = ['h4', 'h4.sc-eDV5Ve', 'h4[class*="Price__PriceValue"]']
        for selector in price_selectors:
            try:
                full_price_text = page.locator(selector).first.inner_text(timeout=5000).strip()
                price_match = re.search(r'₹?([\d,]+)', full_price_text)
                if price_match and price_match.group(1):
                    price_text = price_match.group(1)
                    break
            except: continue

        image_url = ""
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
        description_selectors = ['div[class*="ProductDescription__DescriptionContainer"]', 'div.content']
        for selector in description_selectors:
            try:
                desc_element = page.locator(selector).first
                description = desc_element.inner_text(timeout=5000).strip()
                if description: break
            except: continue

        # --- NEW: Seller Info Extraction ---
        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            # Meesho seller name is often in a specific div structure
            seller_elem = page.locator('div[class*="ShopDetails"] p[class*="ShopName"]').first
            if seller_elem:
                seller_name = seller_elem.inner_text().strip()

            # Rating seems to be nearby, potentially sibling or parent structure
            rating_elem = page.locator('div[class*="ShopDetails"] span[class*="Rating"]').first # Look for span with Rating in class
            if rating_elem:
                 # Rating format might be "4.1 ★"
                 rating_text = rating_elem.inner_text().strip()
                 rating_match = re.search(r'([\d\.]+)', rating_text) # Extract number part
                 if rating_match:
                     seller_rating = f"{rating_match.group(1)} Stars"

            # Review count might be harder, maybe in product reviews section, skip for now
        except Exception as e:
            print(f"[Meesho Scraper] Could not extract seller details: {e}")
        # --- End of Seller Info Extraction ---

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name, # Added
            "seller_rating": seller_rating, # Added
            "seller_review_count": seller_review_count, # Added (likely None)
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = None
        title_selectors = ['h1']
        for selector in title_selectors:
             title = soup.select_one(selector)
             if title: break
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = None
        price_text_raw = ""
        price_selectors = ['h4', 'h4.sc-eDV5Ve', 'h4[class*="Price__PriceValue"]']
        for selector in price_selectors:
             price = soup.select_one(selector)
             if price:
                 price_text_raw = price.get_text().strip()
                 break
        price_text = "0"
        if price_text_raw:
            price_match = re.search(r'₹?([\d,]+)', price_text_raw)
            if price_match and price_match.group(1):
                price_text = price_match.group(1)

        image = None
        image_selectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                 src = image.get('src')
                 if src and src.startswith('http'): break
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = None
        description_selectors = ['div[class*="ProductDescription__DescriptionContainer"]', 'div.content']
        for selector in description_selectors:
            description = soup.select_one(selector)
            if description and description.get_text().strip(): break
        description_text = description.get_text().strip() if description else ""

        # --- NEW: Seller Info Fallback ---
        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_elem = soup.select_one('div[class*="ShopDetails"] p[class*="ShopName"]')
            if seller_elem:
                seller_name = seller_elem.get_text().strip()

            rating_elem = soup.select_one('div[class*="ShopDetails"] span[class*="Rating"]')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'([\d\.]+)', rating_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)} Stars"
        except Exception as e:
             print(f"[Meesho Fallback] Could not extract seller details: {e}")
        # --- End of Seller Info Fallback ---


        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": seller_name, # Added
            "seller_rating": seller_rating, # Added
            "seller_review_count": seller_review_count, # Added (likely None)
        }