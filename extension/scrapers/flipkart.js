// This is the debug message to check if the new script is loading.
console.log("--- FLIPKART SCRAPER v6 (specific price) IS RUNNING ---");

/**
 * Normalizes a price string by removing currency symbols and commas.
 * @param {string} priceStr The price string to normalize.
 * @returns {number} The normalized price as a number.
 */
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    const cleaned = priceStr.replace(/[₹,MRP\s]/g, '').trim();
    const price = parseFloat(cleaned);
    return isNaN(price) ? 0 : price;
}

/**
 * Sends a message from the content script to other parts of the extension.
 * @param {object | null} product The product data to send, or null.
 */
function sendProductInfo(product) {
  // If a product is found with title and price, send it.
  // Otherwise, send `null` to clear stale data.
  if (product && product.title && product.currentPrice > 0) {
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: product });
  } else {
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: null });
  }
}

/**
 * Scrapes the Flipkart product page.
 */
function scrapeFlipkart() {
    let title = '';
    // A list of all known title selectors.
    const titleSelectors = [
        'span.VU-ZEz',   // For laptops and tablets
        'span.B_NuCI'    // For TVs and other items
    ];
    for (const selector of titleSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            title = el.innerText.trim();
            break; 
        }
    }

    let priceText = '';
    // --- THIS LIST IS NOW FIXED ---
    const priceSelectors = [
        'div._30jeq3',              // Most common price
        'div._1vC4OE',             // Older price
        'div.h10eU > div:first-child' // Specific price for laptops/tablets
    ];
    for (const selector of priceSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            priceText = el.innerText.trim();
            break;
        }
    }
    
    let imageUrl = '';
    const imageSelectors = ['img._396cs4', 'img._2r_T1E'];
     for (const selector of imageSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            imageUrl = el.getAttribute('src');
            break;
        }
    }
    
    const description = document.querySelector('._1mXcCf.RmoJUa p')?.innerText || '';

    return { 
        title, 
        currentPrice: normalizePrice(priceText), 
        imageUrl, 
        brand: '', 
        description, 
        source: "Flipkart" 
    };
}

// --- Main execution ---
sendProductInfo(scrapeFlipkart());