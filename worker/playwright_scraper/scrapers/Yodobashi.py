from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class YodobashiScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for Yodobashi.com"""
        
        # --- Set locale to ja-JP ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8"})
        except Exception as e:
            print(f"[Yodobashi Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            page.wait_for_selector('h1#productName', timeout=10000)
            page.wait_for_selector('.productPrice', timeout=10000)
        except Exception as e:
            print(f"[Yodobashi Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('h1#productName').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[Yodobashi Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is usually in a class 'productPrice' or 'price'
            price_elem = page.locator('.productPrice').first
            if not price_elem.is_visible():
                 price_elem = page.locator('.price').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[Yodobashi Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('#productImage').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[Yodobashi Scraper] Could not find image: {e}")

        description = ""
        try:
            # Find the "商品の概要" (Product Overview)
            desc_container = page.locator('#productDetail .productDesc').first
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[Yodobashi Scraper] Could not find description: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "JPY", # Japanese Yen
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": "Yodobashi",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [], # Reviews are complex to parse
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Handles formats like "¥12,800" or "12,800円"
        price_str = re.sub(r'[¥,円\s]', '', price_str).strip()
        
        price_match = re.search(r'(\d+)', price_str)
        if price_match:
            price = int(price_match.group(1))
            return price * 100 # Store 12800 Yen as 1280000
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1#productName')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('.productPrice, .price')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('#productImage')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('#productDetail .productDesc')
        description_text = description.get_text(strip=True) if description else ""
        
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "JPY",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": "Yodobashi",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [],
        }