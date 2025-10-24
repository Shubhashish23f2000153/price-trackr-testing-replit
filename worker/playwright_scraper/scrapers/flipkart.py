from playwright.sync_api import Page
from bs4 import BeautifulSoup
from typing import Dict
from ..base_scraper import BaseScraper


class FlipkartScraper(BaseScraper):
    def extract_data(self, page: Page) -> Dict:
        """Extract data using Playwright"""
        title = ""
        # ... (title finding logic remains the same) ...
        title_selectors = ['span.VU-ZEz', 'span.B_NuCI']
        for selector in title_selectors:
            try:
                title = page.locator(selector).first.inner_text().strip()
                if title: break
            except: continue
        if not title: title = "Unknown Product"


        price_text = ""
        # ... (price finding logic remains the same) ...
        price_selectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj']
        for selector in price_selectors:
            try:
                price_text = page.locator(selector).first.inner_text()
                if price_text: break
            except: continue


        availability = "In Stock"
        # ... (availability finding logic remains the same) ...
        try:
            avail_elem = page.locator('._16FRp0').first
            if avail_elem: availability = avail_elem.inner_text().strip()
        except: pass


        image_url = ""
        # ... (image finding logic remains the same) ...
        image_selectors = ['img.DByuf4', 'img._396cs4._2amPTt._3qGmMb', 'img._2r_T1E', 'img.q6DClP']
        for selector in image_selectors:
            try:
                img_element = page.locator(selector).first
                src = img_element.get_attribute('src')
                if src and src.startswith('http'):
                    image_url = src
                    break
            except: continue


        # --- ADDED DESCRIPTION LOGIC ---
        description = ""
        description_selectors = [
            'div.Xbd0Sd p',          # From image_3fd30b.png
            '._1mXcCf.RmoJUa p',    # Old selector
            'div._1AN87F'          # Bullet points container
        ]
        for selector in description_selectors:
            try:
                desc_element = page.locator(selector).first
                if selector == 'div._1AN87F':
                    # Handle bullet points
                    list_items = desc_element.locator('li._21Ahn-').all_inner_texts()
                    description = "\n".join([f"• {item.strip()}" for item in list_items])
                else:
                    description = desc_element.inner_text().strip()

                if description:
                    break # Found description
            except:
                continue
        # --- END OF DESCRIPTION LOGIC ---


        return {
            "title": title,
            "price": self.normalize_price(price_text) if price_text else 0,
            "currency": "INR",
            "availability": availability,
            "in_stock": "stock" in availability.lower() or "available" in availability.lower(),
            "url": self.url,
            "image_url": image_url,
            "description": description # Added description field
        }

    def extract_data_fallback(self, html: str) -> Dict:
        """Fallback extraction with BeautifulSoup"""
        soup = BeautifulSoup(html, 'lxml')

        # ... (title, price, availability, image logic remains the same) ...
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


        # --- ADDED DESCRIPTION LOGIC ---
        description = ""
        description_selectors = [
            'div.Xbd0Sd p',          # From image_3fd30b.png
            '._1mXcCf.RmoJUa p',    # Old selector
            'div._1AN87F'          # Bullet points container
        ]
        for selector in description_selectors:
            desc_element = soup.select_one(selector)
            if desc_element:
                 if selector == 'div._1AN87F':
                     list_items = desc_element.select('li._21Ahn-')
                     description = "\n".join([f"• {item.get_text().strip()}" for item in list_items])
                 else:
                     description = desc_element.get_text().strip()

                 if description:
                    break # Found description
        # --- END OF DESCRIPTION LOGIC ---

        return {
            "title": title_text,
            "price": self.normalize_price(price_text),
            "currency": "INR",
            "availability": avail_text,
            "in_stock": "stock" in avail_text.lower(),
            "url": self.url,
            "image_url": image_url,
            "description": description # Added description field
        }