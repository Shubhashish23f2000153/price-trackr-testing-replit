// extension/scrapers/rakuten.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Handles "¥1,999" or "1,999円"
    const cleaned = priceStr.replace(/[¥,円\s]/g, '').trim();
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

function scrapeRakuten() {
    const title = document.querySelector('h1.product-title')?.innerText.trim() || '';
    const priceText = document.querySelector('div.price')?.innerText.trim() || '';
    const imageUrl = document.querySelector('img.main-image')?.getAttribute('src') || '';
    
    let brand = 'Rakuten'; // Default
    try {
        brand = document.querySelector('a.shop-name-link')?.innerText.trim() || 
                document.querySelector('a[data-testid="shop-name"]')?.innerText.trim() || 
                brand;
    } catch(e) {}

    const description = document.querySelector('div.product-description')?.innerText.trim() || '';

    return { 
        title, 
        currentPrice: normalizePrice(priceText), 
        imageUrl, 
        brand, 
        description, 
        source: "Rakuten.co.jp" 
    };
}

sendProductInfo(scrapeRakuten());