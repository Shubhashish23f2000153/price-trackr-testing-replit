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

function scrapeMeesho() {
    const title = document.querySelector('span.Text__StyledText-sc-oo0kvp-0.bFfSno')?.innerText.trim() || '';
    const priceText = document.querySelector('h4.Text__StyledText-sc-oo0kvp-0.dLSsNI')?.innerText.trim() || '';
    const imageUrl = document.querySelector('img.styles__StyledImg-sc-1SXP95N-2.dYFjot')?.getAttribute('src') || '';
    return { title, currentPrice: normalizePrice(priceText), imageUrl, brand: '', description: '', source: "Meesho" };
}

sendProductInfo(scrapeMeesho());