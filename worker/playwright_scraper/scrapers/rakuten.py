from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class RakutenScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for Rakuten.co.jp"""
        
        # --- Set locale to ja-JP ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8"})
        except Exception as e:
            print(f"[Rakuten Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            page.wait_for_selector('.product-title', timeout=10000)
            page.wait_for_selector('.price', timeout=10000)
        except Exception as e:
            print(f"[Rakuten Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            # Rakuten often has a complex title structure
            title_elem = page.locator('h1.product-title').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[Rakuten Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is in a div with class 'price'
            price_elem = page.locator('div.price').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[Rakuten Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('img.main-image').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[Rakuten Scraper] Could not find image: {e}")

        seller_name = "Rakuten" # Default
        seller_rating = None
        seller_review_count = None
        try:
            # Find the shop name
            seller_elem = page.locator('a.shop-name-link').first
            if seller_elem:
                seller_name = seller_elem.inner_text().strip()
            else:
                seller_elem = page.locator('a[data-testid="shop-name"]').first
                if seller_elem:
                    seller_name = seller_elem.inner_text().strip()
            
            if "Rakuten" in seller_name:
                seller_rating = "Official Store"

        except Exception as e:
            print(f"[Rakuten Scraper] Could not find seller: {e}")

        description = ""
        try:
            desc_container = page.locator('div.product-description').first
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[Rakuten Scraper] Could not find description: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "JPY", # Japanese Yen
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": [], # Reviews are complex to parse
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Handles formats like "¥1,999" or "1,999円" or "1999"
        # 1. Remove currency symbols, commas, and Japanese Yen symbol
        price_str = re.sub(r'[¥,円\s]', '', price_str).strip()
        
        price_match = re.search(r'(\d+)', price_str)
        if price_match:
            # JPY is a zero-decimal currency, so we multiply by 1
            # But our system stores in "cents", so 1 Yen = 100 "sen" (though sen isn't used)
            # To be consistent, let's treat the base unit as the storable unit.
            # OR, we adjust the system.
            # For now, let's store the raw Yen value * 100
            price = int(price_match.group(1))
            return price * 100 # Store 1999 Yen as 199900
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1.product-title')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('div.price')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('img.main-image')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('div.product-description')
        description_text = description.get_text(strip=True) if description else ""
        
        seller_name = "Rakuten"
        try:
            seller_elem = soup.select_one('a.shop-name-link, a[data-testid="shop-name"]')
            if seller_elem:
                seller_name = seller_elem.get_text(strip=True)
        except:
            pass

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "JPY",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": seller_name,
            "seller_rating": "Official Store" if "Rakuten" in seller_name else None,
            "seller_review_count": None,
            "recent_reviews": [],
        }