from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class VijaySalesScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for VijaySales.com"""
        
        # --- Set locale to en-IN ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "en-IN,en;q=0.9"})
        except Exception as e:
            print(f"[VijaySales Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            page.wait_for_selector('h1[itemprop="name"]', timeout=10000)
            page.wait_for_selector('#ContentPlaceHolder1_div_PriceDetails', timeout=10000)
        except Exception as e:
            print(f"[VijaySales Scraper] Timed out waiting for core elements: {e}")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('h1[itemprop="name"]').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[VijaySales Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is in a span with itemprop="price"
            price_elem = page.locator('span[itemprop="price"]').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[VijaySales Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('#imgmain').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
            elif src:
                 image_url = "https://www.vijaysales.com" + src # Handle relative URLs
        except Exception as e:
            print(f"[VijaySales Scraper] Could not find image: {e}")

        description = ""
        try:
            # Get key features
            desc_elements = page.locator('#ContentPlaceHolder1_div_HighLights li').all()
            desc_lines = [item.inner_text().strip() for item in desc_elements]
            description = "\n".join(desc_lines)
        except Exception as e:
            print(f"[VijaySales Scraper] Could not find description: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR", # Indian Rupee
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": "Vijay Sales",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [], # Reviews not easily accessible
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Handles "₹ 1,19,900" or "119900"
        price_str = re.sub(r'[₹,\s]', '', price_str).strip()
        
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100) # Store 119900 as 11990000
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1[itemprop="name"]')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('span[itemprop="price"]')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('#imgmain')
        image_url = ""
        if image:
            src = image.get('src', '')
            if src and src.startswith('http'):
                image_url = src
            elif src:
                image_url = "https://www.vijaysales.com" + src

        desc_lines = []
        try:
            desc_elements = soup.select('#ContentPlaceHolder1_div_HighLights li')
            desc_lines = [item.get_text().strip() for item in desc_elements]
        except:
            pass
        description_text = "\n".join(desc_lines)
        
        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": "Vijay Sales",
            "seller_rating": "Official Store",
            "seller_review_count": None,
            "recent_reviews": [],
        }