function normalizePrice(priceStr) {
    if (!priceStr) return 0;
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

function scrapeMyntra() {
    const title = document.querySelector('h1.pdp-title')?.innerText.trim() || '';
    const priceText = document.querySelector('span.pdp-price')?.innerText.trim() || '';
    let imageUrl = '';
    const imageEl = document.querySelector('.image-grid-image');
    if (imageEl) {
        const style_attr = imageEl.style.backgroundImage;
        if (style_attr && style_attr.includes('url("')) {
            imageUrl = style_attr.split('url("')[1].split('")')[0];
        }
    }
    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand: '', description: '', source: "Myntra" };
}

sendProductInfo(scrapeMyntra());