// This function sends a message FROM the content script TO other parts of the extension (like the popup)
function sendProductInfo(product) {
  chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product });
}

// --- Site-Specific Scrapers ---

function scrapeAmazon() {
  const titleEl = document.getElementById('productTitle');
  const priceEl = document.querySelector('.a-price-whole, #priceblock_ourprice, #priceblock_dealprice');
  
  if (titleEl && priceEl) {
    const title = titleEl.innerText.trim();
    const price = priceEl.innerText.trim();
    return { title, price, source: "Amazon" };
  }
  return null;
}

function scrapeFlipkart() {
  const titleEl = document.querySelector('.B_NuCI, .VU-ZEz');
  const priceEl = document.querySelector('._30jeq3, ._1vC4OE');

  if (titleEl && priceEl) {
    const title = titleEl.innerText.trim();
    const price = priceEl.innerText.trim();
    return { title, price, source: "Flipkart" };
  }
  return null;
}


// --- Main Logic ---

// This code runs as soon as you load a product page
function runScraper() {
    const host = window.location.hostname;
    let product = null;

    if (host.includes("amazon.in")) {
        product = scrapeAmazon();
    } else if (host.includes("flipkart.com")) {
        product = scrapeFlipkart();
    }

    if (product) {
        sendProductInfo(product);
    }
}

// Run the scraper when the page is loaded
runScraper();