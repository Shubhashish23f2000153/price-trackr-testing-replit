// extension/scrapers/bestbuy.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    const cleaned = priceStr.replace(/[$,\s]/g, '').trim();
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

function scrapeBestBuy() {
    const title = document.querySelector('h1.heading-5')?.innerText.trim() || '';
    
    let priceText = '';
    try {
        // BestBuy price is often split
        const priceDollars = document.querySelector('.priceView-hero-price span[aria-hidden="true"]')?.innerText || '';
        const priceCents = document.querySelector('.priceView-price-MSRP, .priceView-price-small-cents')?.innerText || '';
        priceText = `${priceDollars}${priceCents}`;
        if (!priceDollars) {
             priceText = document.querySelector('.price-box .priceView-hero-price span[aria-hidden="true"]')?.innerText || '';
        }
    } catch (e) {}

    const imageUrl = document.querySelector('img.primary-image')?.getAttribute('src') || '';
    
    let description = '';
    try {
        description = document.querySelector('div[data-testid="product-description"] .html-fragment')?.innerText.trim() || '';
    } catch(e) {}

    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand: 'Best Buy', description, source: "BestBuy.com" };
}

sendProductInfo(scrapeBestBuy());