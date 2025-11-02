from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class BestBuyCAScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for BestBuy.ca"""
        
        # --- Set locale to en-CA ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "en-CA"})
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            # .ca uses a different class for title
            page.wait_for_selector('h1[class*="productName_"]', timeout=10000)
            page.wait_for_selector('span[data-testid="price-current-value"]', timeout=10000) # Price
        except Exception as e:
            print(f"[BestBuyCA Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('h1[class*="productName_"]').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # .ca price is usually a single element
            price_elem = page.locator('span[data-testid="price-current-value"]').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # .ca uses a different image selector
            img_element = page.locator('img[class*="productImage_"]').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not find image: {e}")

        seller_name = "Best Buy" # Default
        seller_rating = "Official Store"
        seller_review_count = None
        try:
            # Check for third-party sellers
            sold_by_elem = page.locator('a[data-testid*="seller-name-link"]').first
            if sold_by_elem:
                seller_name = sold_by_elem.inner_text().strip()
                if "best buy" not in seller_name.lower():
                    seller_rating = None # 3rd party
        except Exception as e:
            pass # Keep default

        description = ""
        try:
            # Find the "About this item" description
            desc_container = page.locator('div[class*="productDescription_"] .overview_')
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not find description: {e}")

        recent_reviews: List[str] = []
        try:
            review_elements = page.locator('[data-testid="review-text-content"]').all()
            for i, review_elem in enumerate(review_elements):
                 if i >= 5: break
                 review_text = review_elem.inner_text().strip()
                 if review_text:
                     recent_reviews.append(review_text)
            print(f"[BestBuyCA Scraper] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[BestBuyCA Scraper] Could not extract reviews: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "CAD", # Canadian Scraper
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews,
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

        title = soup.select_one('h1[class*="productName_"]')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('span[data-testid="price-current-value"]')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('img[class*="productImage_"]')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('div[class*="productDescription_"] .overview_')
        description_text = description.get_text(strip=True) if description else ""
        
        seller_name = "Best Buy"
        try:
            sold_by_elem = soup.select_one('a[data-testid*="seller-name-link"]')
            if sold_by_elem:
                seller_name = sold_by_elem.get_text(strip=True)
        except:
            pass

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "CAD",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": seller_name,
            "seller_rating": "Official Store" if "best buy" in seller_name.lower() else None,
            "seller_review_count": None,
            "recent_reviews": [],
        }