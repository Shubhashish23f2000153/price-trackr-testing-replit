from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class JBHifiScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for JBHiFi.com.au"""
        
        # --- Set locale to en-AU ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "en-AU"})
        except Exception as e:
            print(f"[JBHifi Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            page.wait_for_selector('h1[data-testid="product-title"]', timeout=10000)
            page.wait_for_selector('div[data-testid="price-box"]', timeout=10000)
        except Exception as e:
            print(f"[JBHifi Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---
        
        # --- Strategy 1: Attempt to find JSON-LD (Schema.org) data ---
        try:
            json_ld_element = page.locator('script[type="application/ld+json"]').first
            if json_ld_element:
                json_ld_text = json_ld_element.inner_text()
                json_data = json.loads(json_ld_text)
                
                if json_data.get("@type") == "Product":
                    print("[JBHifi Scraper] Found JSON-LD data. Parsing...")
                    title = json_data.get("name")
                    price_text = json_data.get("offers", {}).get("price")
                    image_url = json_data.get("image")
                    description = json_data.get("description")
                    
                    return {
                        "title": title,
                        "price": self.normalize_price(price_text) if price_text else 0,
                        "currency": "AUD",
                        "availability": "In Stock",
                        "in_stock": True,
                        "url": self.url,
                        "image_url": image_url,
                        "description": description,
                        "seller_name": "JB Hi-Fi",
                        "seller_rating": "Official Store",
                        "seller_review_count": None,
                        "recent_reviews": [], # JSON-LD rarely contains reviews
                    }
        except Exception as e:
            print(f"[JBHifi Scraper] Could not parse JSON-LD, falling back to HTML: {e}")
        # --- End Strategy 1 ---

        # --- Strategy 2: Fallback to HTML scraping ---
        print("[JBHifi Scraper] Parsing HTML...")
        title = "Unknown Product"
        try:
            title_elem = page.locator('h1[data-testid="product-title"]').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[JBHifi Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is in a div with testid 'price-box', get the text
            price_elem = page.locator('div[data-testid="price-box"]').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[JBHifi Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('img[data-testid="hero-image"]').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[JBHifi Scraper] Could not find image: {e}")

        description = ""
        try:
            desc_container = page.locator('div[data-testid="overview-acc-panel"] .product-overview').first
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[JBHifi Scraper] Could not find description: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "AUD", # Australian Scraper
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": "JB Hi-Fi",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [], # Reviews are loaded async, skip for now
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        price_str = re.sub(r'[$,]', '', price_str)
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100)
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1[data-testid="product-title"]')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('div[data-testid="price-box"]')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('img[data-testid="hero-image"]')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('div[data-testid="overview-acc-panel"] .product-overview')
        description_text = description.get_text(strip=True) if description else ""

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "AUD",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": "JB Hi-Fi",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [],
        }