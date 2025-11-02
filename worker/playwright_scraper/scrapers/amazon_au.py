from playwright.sync_api import Page
from bs4 import BeautifulSoup
from ..base_scraper import BaseScraper
from typing import Dict, List
import re

class AmazonAUScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright for Amazon.com.au"""
        
        # --- Set locale to en-AU ---
        try:
            page.context.set_extra_http_headers({"Accept-Language": "en-AU"})
        except Exception as e:
            print(f"[AmazonAU Scraper] Could not set locale: {e}")

        title = "Unknown Product"
        try:
            title = page.locator('#productTitle').first.inner_text().strip()
        except: pass

        price_text = ""
        # Price selectors for amazon.com.au
        price_selectors = ['.a-price-whole', '#priceblock_ourprice', '#priceblock_dealprice', '.a-price .a-offscreen']
        for selector in price_selectors:
            try:
                price_elem = page.locator(selector).first
                if price_elem:
                    price_text = price_elem.inner_text()
                    # .a-offscreen contains the full price with symbol, e.g., $19.99
                    if "$" in price_text:
                        break 
            except: continue
        
        # If price is still split (e.g., $19 and 99)
        if "$" not in price_text:
             try:
                price_symbol = page.locator('.a-price-symbol').first.inner_text().strip()
                if price_symbol == "$":
                    price_whole = page.locator('.a-price-whole').first.inner_text().strip()
                    price_fraction = page.locator('.a-price-fraction').first.inner_text().strip()
                    price_text = f"{price_whole}.{price_fraction}"
             except:
                pass # Use whatever we got in price_text

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
            print(f"[AmazonAU Scraper] Could not extract seller details: {e}")

        recent_reviews: List[str] = []
        try:
            review_elements = page.locator('div[data-hook="review-collapsed"] span').all()
            if not review_elements:
                review_elements = page.locator('.review-text-content span').all()

            for i, review_elem in enumerate(review_elements):
                if i >= 5: break
                review_text = review_elem.inner_text().strip()
                if review_text:
                    recent_reviews.append(review_text)
            print(f"[AmazonAU Scraper] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[AmazonAU Scraper] Could not extract reviews: {e}")

        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "AUD", # <-- Australian Scraper
            "availability": availability,
            "in_stock": "in stock" in availability.lower(),
            "url": self.url,
            "image_url": image_url,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews,
        }

    @staticmethod
    def normalize_price(price_str: str) -> int:
        import re
        # Updated regex to handle $ and ,
        price_str = re.sub(r'[$,]', '', price_str)
        price_match = re.search(r'(\d+\.?\d*)', price_str)
        if price_match:
            price = float(price_match.group(1))
            return int(price * 100)
        return 0

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = soup.select_one('#productTitle')
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = soup.select_one('.a-price .a-offscreen')
        price_text = price.get_text() if price else "0"

        availability = soup.select_one('#availability span')
        avail_text = availability.get_text().strip() if availability else "Unknown"

        image = soup.select_one('#landingImage')
        image_url = image.get('src', '') if image else ""

        seller_name = None
        try:
            seller_link = soup.select_one('#merchant-info a')
            if seller_link: seller_name = seller_link.get_text().strip()
            if not seller_name:
                seller_span = soup.select_one('a#sellerProfileTriggerId')
                if seller_span: seller_name = seller_span.get_text().strip()
        except Exception as e:
             print(f"[AmazonAU Fallback] Could not extract seller details: {e}")

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "AUD", # <-- Australian Scraper
            "availability": avail_text,
            "in_stock": "in stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url,
            "seller_name": seller_name,
            "seller_rating": None,
            "seller_review_count": None,
            "recent_reviews": [],
        }