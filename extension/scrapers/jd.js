// extension/scrapers/jd.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Handles "¥1999.00" or "￥1999"
    const cleaned = priceStr.replace(/[¥,￥\s]/g, '').trim();
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

function scrapeJD() {
    const title = document.querySelector('div.sku-name')?.innerText.trim() || '';
    const priceText = document.querySelector('span.price')?.innerText.trim() || '';
    
    let imageUrl = document.querySelector('#spec-img')?.getAttribute('src') || '';
    if (imageUrl && !imageUrl.startsWith('http')) {
        imageUrl = "https:" + imageUrl; // Fix protocol-less URLs
    }

    const brand = document.querySelector('div.shopName a')?.innerText.trim() || 'JD.com';
    let description = '';
    try {
        const descElements = document.querySelectorAll('ul.parameter2 li');
        description = Array.from(descElements).map(li => li.innerText.trim()).join('\n');
    } catch(e) {}


    return { 
        title, 
        currentPrice: normalizePrice(priceText), 
        imageUrl, 
        brand, 
        description, 
        source: "JD.com" 
    };
}

sendProductInfo(scrapeJD());