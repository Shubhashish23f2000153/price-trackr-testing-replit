from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict
import re # Import regex

class MyntraScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        TITLE_SELECTOR = '.pdp-title'
        PRICE_SELECTOR = '.pdp-price'
        IMAGE_SELECTOR = '.image-grid-image'
        # --- NEW: Seller Selector (Myntra often sells directly, might be tricky) ---
        SELLER_SELECTOR = '.pdp-seller-info a strong' 
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
                style_attr = image_elem.get_attribute('style')
                if style_attr and 'url(' in style_attr:
                     image_url = style_attr.split('url("')[1].split('")')[0]
        except:
            pass

        # --- NEW: Seller Info Extraction ---
        seller_name = None
        seller_rating = None # Myntra doesn't typically show ratings this way
        seller_review_count = None
        try:
            seller_elem = page.locator(SELLER_SELECTOR).first
            seller_name = seller_elem.inner_text().strip()
            # If seller name contains "Myntra" or similar, it's likely first-party
            if seller_name and ('myntra' in seller_name.lower()):
                 seller_rating = "Official Store" # Indicate first-party
            # If it's a generic seller, try to find a rating if available elsewhere (unlikely)

        except Exception as e:
            # Often fails if Myntra is the seller, which is common
            # print(f"[Myntra Scraper] Could not extract seller details (might be Myntra): {e}")
            # Assume Myntra if no seller found
            seller_name = "Myntra"
            seller_rating = "Official Store"
        # --- End of Seller Info Extraction ---


        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "seller_name": seller_name, # Added
            "seller_rating": seller_rating, # Added
            "seller_review_count": seller_review_count, # Added (likely None)
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')
        
        title = soup.select_one('.pdp-title')
        title_text = title.get_text().strip() if title else "Unknown Product"
        
        price = soup.select_one('.pdp-price')
        price_text = price.get_text() if price else "0"
        
        # --- NEW: Seller Info Fallback ---
        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_elem = soup.select_one('.pdp-seller-info a strong')
            if seller_elem:
                seller_name = seller_elem.get_text().strip()
                if seller_name and ('myntra' in seller_name.lower()):
                    seller_rating = "Official Store"
            else:
                 seller_name = "Myntra" # Assume Myntra if not found
                 seller_rating = "Official Store"
        except Exception as e:
             # print(f"[Myntra Fallback] Could not extract seller details: {e}")
             seller_name = "Myntra"
             seller_rating = "Official Store"
        # --- End of Seller Info Fallback ---

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": "", # Fallback image is hard
            "seller_name": seller_name, # Added
            "seller_rating": seller_rating, # Added
            "seller_review_count": seller_review_count, # Added (likely None)
        }