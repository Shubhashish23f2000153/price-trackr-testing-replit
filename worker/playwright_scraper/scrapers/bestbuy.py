from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re
import json

class BestBuyScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        
        # --- Wait for core elements to be ready ---
        try:
            page.wait_for_selector('h1.heading-5', timeout=10000) # Title
            page.wait_for_selector('.priceView-hero-price span[aria-hidden="true"]', timeout=10000) # Price
        except Exception as e:
            print(f"[BestBuy Scraper] Timed out waiting for core elements: {e}")
            # Continue anyway, maybe it's just a different layout
        # --- End Wait ---

        title = "Unknown Product"
        try:
            title_elem = page.locator('h1.heading-5').first
            title = title_elem.inner_text().strip()
        except Exception as e:
            print(f"[BestBuy Scraper] Could not find title: {e}")

        price_text = ""
        try:
            # BestBuy price is often split into dollars and cents
            price_dollars = page.locator('.priceView-hero-price span[aria-hidden="true"]').first.inner_text()
            price_cents = page.locator('.priceView-price-MSRP, .priceView-price-small-cents').first.inner_text()
            price_text = f"{price_dollars}{price_cents}"
            if not price_dollars:
                raise Exception("Price dollars not found")
        except Exception as e:
            print(f"[BestBuy Scraper] Could not find standard price, trying alt: {e}")
            try:
                # Fallback for "Clearance" or other price displays
                price_text = page.locator('.price-box .priceView-hero-price span[aria-hidden="true"]').first.inner_text()
            except Exception as e2:
                print(f"[BestBuy Scraper] Could not find any price: {e2}")

        image_url = ""
        try:
            # Main product image
            img_element = page.locator('img.primary-image').first
            src = img_element.get_attribute('src')
            if src and src.startswith('http'):
                image_url = src
        except Exception as e:
            print(f"[BestBuy Scraper] Could not find image: {e}")

        seller_name = "Best Buy" # Default
        seller_rating = "Official Store"
        seller_review_count = None
        try:
            # Check for third-party sellers
            sold_by_elem = page.locator('div[data-testid="sold-by-value"] a').first
            if sold_by_elem:
                seller_name = sold_by_elem.inner_text().strip()
                if "best buy" not in seller_name.lower():
                    seller_rating = None # 3rd party
        except Exception as e:
            pass # Keep default

        description = ""
        try:
            # Find the "About this item" description
            desc_container = page.locator('div[data-testid="product-description"] .html-fragment').first
            description = desc_container.inner_text().strip()
        except Exception as e:
            print(f"[BestBuy Scraper] Could not find description: {e}")

        recent_reviews: List[str] = []
        try:
            review_elements = page.locator('.review-item .review-text').all()
            for i, review_elem in enumerate(review_elements):
                 if i >= 5: break
                 review_text = review_elem.inner_text().strip()
                 if review_text:
                     recent_reviews.append(review_text)
            print(f"[BestBuy Scraper] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[BestBuy Scraper] Could not extract reviews: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "USD", # US Scraper
            "availability": "In Stock", # Assume in stock if price is visible
            "in_stock": True,
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews,
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('h1.heading-5')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price_text = ""
        try:
            price_dollars = soup.select_one('.priceView-hero-price span[aria-hidden="true"]').get_text()
            price_cents = soup.select_one('.priceView-price-MSRP, .priceView-price-small-cents').get_text()
            price_text = f"{price_dollars}{price_cents}"
        except Exception:
             pass # Price is hard to get in fallback

        image = soup.select_one('img.primary-image')
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = soup.select_one('div[data-testid="product-description"] .html-fragment')
        description_text = description.get_text(strip=True) if description else ""
        
        seller_name = "Best Buy"
        try:
            sold_by_elem = soup.select_one('div[data-testid="sold-by-value"] a')
            if sold_by_elem:
                seller_name = sold_by_elem.get_text(strip=True)
        except:
            pass

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "USD",
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