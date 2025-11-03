from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict
import re
import time

class MeeshoScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        # --- 1. INCREASED TIMEOUT to 20 seconds ---
        try:
            price_selector_to_wait = 'h4[class*="Price__PriceValue"], h4.sc-eDV5Ve, .NewProductCard__PriceRow-sc'
            page.wait_for_selector(price_selector_to_wait, timeout=20000)
        except Exception as e:
            print(f"[Meesho Scraper] Timed out waiting for price element: {e}")
            # Continue anyway, maybe it's there
        # --- END WAIT ---

        title = ""
        title_selectors = ['h1', 'span.NewProductCard__ProductTitle_pdp-sc']
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text(timeout=10000).strip()
                if title: break
            except: continue
        if not title: title = "Unknown Product"

        price_text = ""
        price_selectors = ['h4[class*="Price__PriceValue"]', 'h4.sc-eDV5Ve', 'h4', '.NewProductCard__PriceRow-sc']
        for selector in price_selectors:
            try:
                full_price_text = page.locator(selector).first.inner_text(timeout=10000).strip()
                price_match = re.search(r'₹?([\d,]+)', full_price_text)
                if price_match and price_match.group(1):
                    price_text = price_match.group(1)
                    break
            except: continue

        image_url = ""
        image_selectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img', 'img.NewProductCard__Image-sc']
        for selector in image_selectors:
            try:
                img_element = page.locator(selector).first
                src = img_element.get_attribute('src', timeout=10000)
                if src and src.startswith('http'):
                    image_url = src
                    break
            except: continue

        # --- 2. REMOVED DESCRIPTION SCRAPING (it's slow and fails) ---
        description = ""

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            # --- 3. SIMPLIFIED SELLER LOGIC (faster) ---
            seller_elem = page.locator('div[class*="ShopDetails"] p[class*="ShopName"], .ProductSellerInformation__Name-sc').first
            seller_name = seller_elem.inner_text(timeout=5000).strip()

            rating_elem = page.locator('div[class*="ShopDetails"] span[class*="Rating"], .ProductSellerInformation__Rating-sc').first
            rating_text = rating_elem.inner_text(timeout=5000).strip()
            rating_match = re.search(r'([\d\.]+)', rating_text)
            if rating_match:
                seller_rating = f"{rating_match.group(1)} Stars"
        except Exception as e:
            # This is not critical, so we just print a warning
            print(f"[Meesho Scraper] Could not extract seller details (non-critical): {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description, # Will be empty
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = None
        title_selectors = ['h1', 'span.NewProductCard__ProductTitle_pdp-sc']
        for selector in title_selectors:
             title = soup.select_one(selector)
             if title: break
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = None
        price_text_raw = ""
        price_selectors = ['h4[class*="Price__PriceValue"]', 'h4.sc-eDV5Ve', 'h4', '.NewProductCard__PriceRow-sc']
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
        image_selectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img', 'img.NewProductCard__Image-sc']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                 src = image.get('src')
                 if src and src.startswith('http'): break
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        # --- REMOVED DESCRIPTION FALLBACK ---
        description_text = ""

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_elem = soup.select_one('div[class*="ShopDetails"] p[class*="ShopName"], .ProductSellerInformation__Name-sc')
            if seller_elem:
                seller_name = seller_elem.get_text().strip()

            rating_elem = soup.select_one('div[class*="ShopDetails"] span[class*="Rating"], .ProductSellerInformation__Rating-sc')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'([\d\.]+)', rating_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)} Stars"
        except Exception as e:
             print(f"[Meesho Fallback] Could not extract seller details {e}")


        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": "In Stock",
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description_text,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
        }