from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict
import re # Import regex

class SnapdealScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        TITLE_SELECTOR = '.pdp-e-i-head'
        PRICE_SELECTOR = '.payBlkBig'
        IMAGE_SELECTOR = '#bx-slider-left-image-panel .cloudzoom'
        # --- NEW: Seller Selectors ---
        SELLER_NAME_SELECTOR = '.pdp-e-seller-name span' # Check if this is correct
        SELLER_RATING_SELECTOR = '.pdp-seller-rating-count' # Might contain count or rating
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

        # --- NEW: Seller Info Extraction ---
        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_elem = page.locator(SELLER_NAME_SELECTOR).first
            seller_name = seller_elem.inner_text().strip()
            if seller_name.lower() == 'snapdeal': # Check if it's Snapdeal itself
                seller_rating = "Official Store"

            # Snapdeal might show rating like "(4.1)" or just review count
            rating_elem = page.locator(SELLER_RATING_SELECTOR).first
            if rating_elem:
                rating_text = rating_elem.inner_text().strip()
                # Try to extract a rating like (X.X)
                rating_match = re.search(r'\(([\d\.]+)\)', rating_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)} Stars"
                else:
                    # Maybe it's just a count?
                    count_match = re.search(r'(\d+,?\d+)', rating_text)
                    if count_match:
                        seller_review_count = count_match.group(1).replace(',', '')
                        # Assign generic rating if only count found? Or leave as None?
                        # seller_rating = "Rated" # Example

        except Exception as e:
            print(f"[Snapdeal Scraper] Could not extract seller details: {e}")
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
            "seller_review_count": seller_review_count, # Added
        }
    
    def extract_data_fallback(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'lxml')
        title = soup.select_one('.pdp-e-i-head')
        title_text = title.get_text().strip() if title else "Unknown Product"
        price = soup.select_one('.payBlkBig')
        price_text = price.get_text() if price else "0"

        # --- NEW: Seller Info Fallback ---
        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_elem = soup.select_one('.pdp-e-seller-name span')
            if seller_elem:
                seller_name = seller_elem.get_text().strip()
                if seller_name.lower() == 'snapdeal':
                    seller_rating = "Official Store"

            rating_elem = soup.select_one('.pdp-seller-rating-count')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'\(([\d\.]+)\)', rating_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)} Stars"
                else:
                    count_match = re.search(r'(\d+,?\d+)', rating_text)
                    if count_match:
                        seller_review_count = count_match.group(1).replace(',', '')

        except Exception as e:
             print(f"[Snapdeal Fallback] Could not extract seller details: {e}")
        # --- End of Seller Info Fallback ---

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": "", # Image fallback is hard
            "seller_name": seller_name, # Added
            "seller_rating": seller_rating, # Added
            "seller_review_count": seller_review_count, # Added
        }