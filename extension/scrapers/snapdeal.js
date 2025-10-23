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

function scrapeSnapdeal() {
    const title = document.querySelector('h1.pdp-e-i-head')?.innerText.trim() || '';
    const priceText = document.querySelector('span.payBlkBig')?.innerText.trim() || '';
    const imageUrl = document.querySelector('img.cloudzoom')?.getAttribute('src') || '';
    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand: '', description: '', source: "Snapdeal" };
}

sendProductInfo(scrapeSnapdeal());