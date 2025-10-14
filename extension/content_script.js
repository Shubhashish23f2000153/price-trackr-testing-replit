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
 * @param {object} product The product data to send.
 */
function sendProductInfo(product) {
  if (product && product.title && product.currentPrice > 0) {
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product });
  }
}

// --- Site-Specific Scrapers ---

function scrapeAmazon() {
    const title = document.getElementById('productTitle')?.innerText.trim() || '';
    
    // Complex price finding logic for Amazon's varied layouts
    let priceText = '';
    const priceSelectors = [
        '.a-price-whole',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '.a-price .a-offscreen'
    ];
    for (const selector of priceSelectors) {
        const priceEl = document.querySelector(selector);
        if (priceEl) {
            priceText = priceEl.innerText;
            break;
        }
    }

    const imageUrl = document.getElementById('landingImage')?.getAttribute('src') || '';
    const brandEl = document.querySelector('#bylineInfo');
    const brand = brandEl ? brandEl.innerText.replace('Visit the', '').replace('Store', '').trim() : '';

    // Find description from feature bullets
    const descriptionBullets = Array.from(document.querySelectorAll('#feature-bullets .a-list-item'));
    const description = descriptionBullets.map(li => li.innerText.trim()).join('\n');

    return {
        title,
        currentPrice: normalizePrice(priceText),
        imageUrl,
        brand,
        description,
        source: "Amazon"
    };
}

function scrapeFlipkart() {
    const title = document.querySelector('.B_NuCI, .VU-ZEz')?.innerText.trim() || '';
    const priceText = document.querySelector('._30jeq3, ._1vC4OE')?.innerText.trim() || '';
    const imageUrl = document.querySelector('._396cs4._2amPTt._3qGmMb')?.getAttribute('src') || '';
    
    // Flipkart brand and description are often less consistently placed
    const brand = ''; // Placeholder - can be improved with more specific selectors
    const description = document.querySelector('._1mXcCf.RmoJUa p')?.innerText || '';

    return {
        title,
        currentPrice: normalizePrice(priceText),
        imageUrl,
        brand,
        description,
        source: "Flipkart"
    };
}


// --- Main Logic ---

function runScraper() {
    const host = window.location.hostname;
    let product = null;

    if (host.includes("amazon.in")) {
        product = scrapeAmazon();
    } else if (host.includes("flipkart.com")) {
        product = scrapeFlipkart();
    }

    if (product) {
        sendProductInfo(product);
    }
}

runScraper();