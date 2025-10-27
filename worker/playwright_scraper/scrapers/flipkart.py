from playwright.sync_api import Page
from bs4 import BeautifulSoup
from typing import Dict, List # Import List
from ..base_scraper import BaseScraper
import re


class FlipkartScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        title_selectors = ['span.VU-ZEz', 'span.B_NuCI']
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text().strip()
                if title: break
            except: continue
        if not title: title = "Unknown Product"


        price_text = ""
        price_selectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj']
        for selector in price_selectors:
            try:
                price_text = page.locator(selector).first.inner_text()
                if price_text: break
            except: continue


        availability = "In Stock"
        try:
            avail_elem = page.locator('._16FRp0').first
            if avail_elem: availability = avail_elem.inner_text().strip()
        except: pass


        image_url = ""
        image_selectors = ['img.DByuf4', 'img._396cs4._2amPTt._3qGmMb', 'img._2r_T1E', 'img.q6DClP']
        for selector in image_selectors:
            try:
                img_element = page.locator(selector).first
                src = img_element.get_attribute('src')
                if src and src.startswith('http'):
                    image_url = src
                    break
            except: continue


        description = ""
        description_selectors = ['div.Xbd0Sd p', '._1mXcCf.RmoJUa p', 'div._1AN87F']
        for selector in description_selectors:
            try:
                desc_element = page.locator(selector).first
                if selector == 'div._1AN87F':
                    list_items = desc_element.locator('li._21Ahn-').all_inner_texts()
                    description = "\n".join([f"• {item.strip()}" for item in list_items])
                else:
                    description = desc_element.inner_text().strip()
                if description: break
            except: continue

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_name_elem = page.locator('#sellerName a span').first # Often inside a span now
            if not seller_name_elem: # Fallback selector
                seller_name_elem = page.locator('#sellerName a').first
            if seller_name_elem:
                seller_name = seller_name_elem.inner_text().strip()

            rating_elem = page.locator('#sellerName ~ div > span').first
            if rating_elem:
                seller_rating = rating_elem.inner_text().strip() # Format is often just "4.1"
                # Extract numeric part if needed later for calculation
                rating_match = re.search(r'([\d\.]+)', seller_rating)
                if rating_match:
                    seller_rating_num = float(rating_match.group(1)) # Example: store numeric too
                
        except Exception as e:
            print(f"[Flipkart Scraper] Could not extract seller details: {e}")

        # --- NEW: Extract Recent Reviews ---
        recent_reviews: List[str] = []
        try:
            # Selector for review text content (might need adjustment)
            review_elements = page.locator('div.t-ZTKy div div').all() # Look for divs inside the review body
            if not review_elements: # Try another common structure
                 review_elements = page.locator('div._6K-7Co').all()

            for i, review_elem in enumerate(review_elements):
                if i >= 5: break
                # Sometimes there's a "READ MORE", get text before that
                full_text = review_elem.inner_text().strip()
                # Simple split, might need refinement
                review_text = full_text.split("READ MORE")[0].strip()
                if review_text:
                    recent_reviews.append(review_text)
            print(f"[Flipkart Scraper] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[Flipkart Scraper] Could not extract reviews: {e}")
        # --- End Extract Recent Reviews ---


        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "stock" in availability.lower() or "available" in availability.lower(),
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count, # Flipkart doesn't always show count easily here
            "recent_reviews": recent_reviews, # Added review list
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        title = None
        title_selectors = ['span.VU-ZEz', 'span.B_NuCI']
        for selector in title_selectors:
             title = soup.select_one(selector)
             if title: break
        title_text = title.get_text().strip() if title else "Unknown Product"

        price = None
        price_selectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj']
        for selector in price_selectors:
             price = soup.select_one(selector)
             if price: break
        price_text = price.get_text() if price else "0"

        availability = soup.select_one('._16FRp0')
        avail_text = availability.get_text().strip() if availability else "In Stock"

        image = None
        image_selectors = ['img.DByuf4', 'img._396cs4._2amPTt._3qGmMb', 'img._2r_T1E', 'img.q6DClP']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                 src = image.get('src')
                 if src and src.startswith('http'): break
        image_url = image.get('src', '') if image and image.get('src', '').startswith('http') else ""

        description = ""
        description_selectors = ['div.Xbd0Sd p', '._1mXcCf.RmoJUa p', 'div._1AN87F']
        for selector in description_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                 if selector == 'div._1AN87F':
                     list_items = desc_element.select('li._21Ahn-')
                     description = "\n".join([f"• {item.get_text().strip()}" for item in list_items])
                 else:
                     description = desc_element.get_text().strip()
                 if description: break

        seller_name = None
        seller_rating = None
        seller_review_count = None
        try:
            seller_name_elem = soup.select_one('#sellerName a span') # Try span first
            if not seller_name_elem:
                seller_name_elem = soup.select_one('#sellerName a')
            if seller_name_elem:
                seller_name = seller_name_elem.get_text().strip()

            rating_elem = soup.select_one('#sellerName ~ div > span')
            if rating_elem:
                seller_rating = rating_elem.get_text().strip()
        except Exception as e:
            print(f"[Flipkart Fallback] Could not extract seller details: {e}")

        # --- NEW: Extract Recent Reviews (Fallback) ---
        recent_reviews: List[str] = []
        try:
            review_elements = soup.select('div.t-ZTKy div div, div._6K-7Co')
            for i, review_elem in enumerate(review_elements):
                 if i >= 5: break
                 full_text = review_elem.get_text().strip()
                 review_text = full_text.split("READ MORE")[0].strip()
                 if review_text:
                     recent_reviews.append(review_text)
            print(f"[Flipkart Fallback] Extracted {len(recent_reviews)} review snippets.")
        except Exception as e:
            print(f"[Flipkart Fallback] Could not extract reviews: {e}")
        # --- End Extract Recent Reviews ---

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url,
            "description": description,
            "seller_name": seller_name,
            "seller_rating": seller_rating,
            "seller_review_count": seller_review_count,
            "recent_reviews": recent_reviews, # Added review list
        }