// extension/scrapers/amazon_ca.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Handles $ and commas
    const cleaned = priceStr.replace(/[$,MRP\s]/g, '').trim();
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
        '.a-price .a-offscreen' // Catches the full price like $19.99
    ];
    for (const selector of priceSelectors) {
        const priceEl = document.querySelector(selector);
        if (priceEl) { 
            priceText = priceEl.innerText; 
            if(priceText.includes('$')) break; // Prefer the one with the symbol
        }
    }
    const imageUrl = document.getElementById('landingImage')?.getAttribute('src') || '';
    const brand = document.querySelector('#bylineInfo')?.innerText.replace('Visit the', '').replace('Store', '').trim() || '';

    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand, description: '', source: "Amazon.ca" };
}

sendProductInfo(scrapeAmazon());