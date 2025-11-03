// extension/scrapers/amazon_com.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Look for $ instead of ₹
    const cleaned = priceStr.replace(/[£,MRP\s]/g, '').trim();
    const price = parseFloat(cleaned);
    return isNaN(price) ? 0 : price;
}

function sendProductInfo(product) {
  if (product && product.title && product.currentPrice > 0) {
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: product });
  } else {
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: null });
  }
}

function scrapeAmazon() {
    const title = document.getElementById('productTitle')?.innerText.trim() || '';
    let priceText = '';
    const priceSelectors = [
        '.a-price-whole',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '.a-price .a-offscreen'
    ];
    for (const selector of priceSelectors) {
        const priceEl = document.querySelector(selector);
        if (priceEl) { priceText = priceEl.innerText; break; }
    }
    const imageUrl = document.getElementById('landingImage')?.getAttribute('src') || '';
    const brandEl = document.querySelector('#bylineInfo');
    const brand = brandEl ? brandEl.innerText.replace('Visit the', '').replace('Store', '').trim() : '';
    const descriptionBullets = Array.from(document.querySelectorAll('#feature-bullets .a-list-item'));
    const description = descriptionBullets.map(li => li.innerText.trim()).join('\n');

    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand, description, source: "Amazon.com" };
}

sendProductInfo(scrapeAmazon());