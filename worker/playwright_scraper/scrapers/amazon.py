from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List # Import List
import re

class AmazonScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = "Unknown Product"
        try:
            title = page.locator('#productTitle').first.inner_text().strip()
        except: pass

        price_text = ""
        price_selectors = ['.a-price-whole', '#priceblock_ourprice', '#priceblock_dealprice', '.a-price .a-offscreen']
        for selector in price_selectors:
            try:
                price_elem = page.locator(selector).first
                if price_elem:
                    price_text = price_elem.inner_text()
                    break
            except: continue

        availability = "Unknown"
        try:
            avail_elem = page.locator('#availability span').first
            if avail_elem: availability = avail_elem.inner_text().strip()
        except: pass

        image_url = ""
        try:
            image_elem = page.locator('#landingImage').first
            if image_elem: image_url = image_elem.get_attribute('src')
        except: pass

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_link = page.locator('#merchant-info a').first
            if seller_link: seller_name = seller_link.inner_text().strip()
            if not seller_name:
                 seller_span = page.locator('a#sellerProfileTriggerId').first
                 if seller_span: seller_name = seller_span.inner_text().strip()

            rating_text_elem = page.locator('#merchant-info').first
            if rating_text_elem:
                 rating_text = rating_text_elem.inner_text()
                 rating_match = re.search(r'(\d+)% positive.*?\((\d+,?\d*) ratings\)', rating_text)
                 if rating_match:
                     seller_rating = f"{rating_match.group(1)}% Positive"
                     seller_review_count = rating_match.group(2).replace(',', '')
        except Exception as e:
            print(f"[Amazon Scraper] Could not extract seller details: {e}")

        # --- NEW: Extract Recent Reviews ---
        recent_reviews: List[str] = []
        try:
            # Selector for individual review text bodies (might need adjustment)
            review_elements = page.locator('div[data-hook="review-collapsed"] span').all()
            if not review_elements: # Try another common selector
                review_elements = page.locator('.review-text-content span').all()

            # Limit to first 3-5 reviews found
            for i, review_elem in enumerate(review_elements):
                if i >= 5: break # Limit number of reviews
                review_text = review_elem.inner_text().strip()
                if review_text:
                    recent_reviews.append(review_text)
            print(f"[Amazon Scraper] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[Amazon Scraper] Could not extract reviews: {e}")
        # --- End Extract Recent Reviews ---

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "in stock" in availability.lower(),
            "url": self.url,
            "image_url": image_url,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews, # Added review list
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('#productTitle')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('.a-price-whole, #priceblock_ourprice')
        price_text = price.get_text() if price else "0"

        availability = soup.select_one('#availability span')
        avail_text = availability.get_text().strip() if availability else "Unknown"

        image = soup.select_one('#landingImage')
        image_url = image.get('src', '') if image else ""

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_link = soup.select_one('#merchant-info a')
            if seller_link: seller_name = seller_link.get_text().strip()
            if not seller_name:
                seller_span = soup.select_one('a#sellerProfileTriggerId')
                if seller_span: seller_name = seller_span.get_text().strip()

            rating_text_elem = soup.select_one('#merchant-info')
            if rating_text_elem:
                rating_text = rating_text_elem.get_text()
                rating_match = re.search(r'(\d+)% positive.*?\((\d+,?\d*) ratings\)', rating_text)
                if rating_match:
                    seller_rating = f"{rating_match.group(1)}% Positive"
                    seller_review_count = rating_match.group(2).replace(',', '')
        except Exception as e:
             print(f"[Amazon Fallback] Could not extract seller details: {e}")

        # --- NEW: Extract Recent Reviews (Fallback) ---
        recent_reviews: List[str] = []
        try:
            review_elements = soup.select('div[data-hook="review-collapsed"] span, .review-text-content span')
            for i, review_elem in enumerate(review_elements):
                 if i >= 5: break
                 review_text = review_elem.get_text().strip()
                 if review_text:
                     recent_reviews.append(review_text)
            print(f"[Amazon Fallback] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[Amazon Fallback] Could not extract reviews: {e}")
        # --- End Extract Recent Reviews ---

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "in stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews, # Added review list
        }