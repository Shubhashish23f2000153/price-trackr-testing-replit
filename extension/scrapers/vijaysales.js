// extension/scrapers/vijaysales.js
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Handles "₹ 1,19,900" or "119900"
    const cleaned = priceStr.replace(/[₹,MRP\s]/g, '').trim();
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

function scrapeVijaySales() {
    const title = document.querySelector('h1[itemprop="name"]')?.innerText.trim() || '';
    const priceText = document.querySelector('span[itemprop="price"]')?.innerText.trim() || '';
    
    let imageUrl = document.querySelector('#imgmain')?.getAttribute('src') || '';
    if (imageUrl && !imageUrl.startsWith('http')) {
        imageUrl = "https://www.vijaysales.com" + imageUrl;
    }

    let description = '';
    try {
        const descElements = document.querySelectorAll('#ContentPlaceHolder1_div_HighLights li');
        description = Array.from(descElements).map(li => li.innerText.trim()).join('\n');
    } catch(e) {}

    return { 
        title, 
        currentPrice: normalizePrice(priceText), 
        imageUrl, 
        brand: 'Vijay Sales', // Default
        description, 
        source: "Vijay Sales" 
    };
}

sendProductInfo(scrapeVijaySales());