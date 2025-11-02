from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class JDScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for JD.com"""
        
        # --- Set locale to zh-CN ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
        except Exception as e:
            print(f"[JD Scraper] Could not set locale: {e}")

        # --- Wait for core elements ---
        try:
            # Wait for either the main title or the price
            page.wait_for_selector('div.sku-name, .price', timeout=15000)
        except Exception as e:
            print(f"[JD Scraper] Timed out waiting for core elements: {e}")
            print("[JD Scraper] WARNING: JD.com is likely blocking the scraper. Data will be incomplete.")
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('div.sku-name').first
            title = title_elem.inner_text().strip()
            if not title:
                # Try fallback title selector
                title_elem = page.locator('.itemInfo-wrap .sku-name').first
                title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[JD Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # Price is often dynamic. Look for a span with 'price'
            price_elem = page.locator('span.price').first
            price_text = price_elem.inner_text().strip()
        except Exception as e:
            print(f"[JD Scraper] Could not find price: {e}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('#spec-img').first
            src = img_element.get_attribute('src')
            if src and not src.startswith('http'):
                src = "https:" + src # JD often uses protocol-less URLs
            
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[JD Scraper] Could not find image: {e}")

        seller_name = "JD.com" # Default (京东自营 - JD Self-operated)
        seller_rating = "Official Store"
        seller_review_count = None
        try:
            # Find the shop name
            seller_elem = page.locator('div.shopName a').first
            if seller_elem:
                seller_name = seller_elem.inner_text().strip()
                if "京东" not in seller_name: # "京东" is Jingdong
                    seller_rating = None # 3rd party
        except Exception as e:
            pass # Keep default

        description = ""
        try:
            # Description is usually in specification list
            spec_items = page.locator('ul.parameter2 li').all()
            desc_lines = [item.inner_text().strip() for item in spec_items[:10]] # Get first 10 specs
            description = "\n".join(desc_lines)
        except Exception as e:
            print(f"[JD Scraper] Could not find description specs: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "CNY", # Chinese Yuan
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": [], # Reviews are heavily protected
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Handles formats like "¥1999.00" or "1999"
        price_str = re.sub(r'[¥,￥\s]', '', price_str).strip()
        
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100) # Store 1999.00 Yuan as 199900
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup (unlikely to work for JD)"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('div.sku-name, .itemInfo-wrap .sku-name')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('span.price')
        price_text = price.get_text() if price else "0"

        image = soup.select_one('#spec-img')
        image_url = image.get('src', '') if image else ""
        if image_url and not image_url.startswith('http'):
            image_url = "https:" + image_url
            
        seller_name = "JD.com"
        try:
            seller_elem = soup.select_one('div.shopName a')
            if seller_elem:
                seller_name = seller_elem.get_text(strip=True)
        except:
            pass

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "CNY",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": "",
            "seller_name": seller_name,
            "seller_rating": "Official Store" if "京东" in seller_name else None,
            "seller_review_count": None,
            "recent_reviews": [],
        }