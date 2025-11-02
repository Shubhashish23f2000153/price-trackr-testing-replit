from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class MediaMarktDEScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for MediaMarkt.de"""
        
        # --- Set locale to de-DE ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "de-DE,de;q=0.9,en;q=0.8"})
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            page.wait_for_selector('h1[data-test="product-title"]', timeout=10000)
            page.wait_for_selector('span[data-test="price-box-current-price"]', timeout=10000)
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('h1[data-test="product-title"]').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is in a span with testid 'price-box-current-price'
            price_elem = page.locator('span[data-test="price-box-current-price"]').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('img[data-test="product-image"]').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Could not find image: {e}")

        description = ""
        try:
            # Find the "Produktbeschreibung" (Product Description)
            desc_container = page.locator('div[data-test="product-description"]').first
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[MediaMarktDE Scraper] Could not find description: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "EUR", # Euro Scraper
            "availability": "In Stock", # Assume in stock
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": "MediaMarkt",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [], # Reviews are not a priority for this site
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Handles formats like "1.999,99" or "19,99"
        # 1. Remove currency symbols, whitespace, and thousand separators (.)
        price_str = re.sub(r'[€\s\.]', '', price_str).strip()
        # 2. Replace comma decimal separator with a dot
        price_str = price_str.replace(',', '.')
        
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100)
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1[data-test="product-title"]')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('span[data-test="price-box-current-price"]')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('img[data-test="product-image"]')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('div[data-test="product-description"]')
        description_text = description.get_text(strip=True) if description else ""

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "EUR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": "MediaMarkt",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [],
        }