// extension/scrapers/yodobashi.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Handles "¥12,800" or "12,800円"
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

function scrapeYodobashi() {
    const title = document.querySelector('h1#productName')?.innerText.trim() || '';
    
    let priceText = document.querySelector('.productPrice')?.innerText.trim() || 
                    document.querySelector('.price')?.innerText.trim() || '';

    const imageUrl = document.querySelector('#productImage')?.getAttribute('src') || '';
    const brand = 'Yodobashi'; // Default
    const description = document.querySelector('#productDetail .productDesc')?.innerText.trim() || '';

    return { 
        title, 
        currentPrice: normalizePrice(priceText), 
        imageUrl, 
        brand, 
        description, 
        source: "Yodobashi.com" 
    };
}

sendProductInfo(scrapeYodobashi());
