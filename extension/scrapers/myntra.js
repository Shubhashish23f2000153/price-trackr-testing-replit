// extension/scrapers/myntra.js

// Debug message to check if script is running
console.log("--- MYNTRA SCRAPER v2 (Hybrid Polling) IS RUNNING ---");

// Global variable to store the last known title *successfully scraped*
let lastSuccessfullyScrapedTitle = "";
// Flag to prevent multiple scrape attempts per navigation
let scrapeAttemptedForCurrentNavigation = false;
// Flag to prevent sending duplicate info if multiple triggers fire
let hasSentInfoForThisScrape = false;

/**
 * Normalizes a price string by removing currency symbols and commas.
 */
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    // Updated to handle 'MRP' and other symbols
    const cleaned = priceStr.replace(/[₹,MRP\s]/g, '').trim();
    const price = parseFloat(cleaned);
    return isNaN(price) ? 0 : price;
}

/**
 * Sends product info (or null) to the background script.
 * Updates lastSuccessfullyScrapedTitle ONLY on success.
 */
function sendProductInfo(product, context = "Unknown") {
  if (hasSentInfoForThisScrape) {
      // console.log(`(${context}) Blocked duplicate sendProductInfo call.`);
      return;
  }
  hasSentInfoForThisScrape = true; // Set flag immediately

  console.log(`(${context}) Sending data to background:`, product);
  chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: product });

  if (product && product.title && product.currentPrice > 0) {
    console.log(`(${context}) ✅ Scrape successful. Updating lastSuccessfullyScrapedTitle.`);
    lastSuccessfullyScrapedTitle = product.title;
  } else {
    let failureReason = [];
    if (!product?.title) failureReason.push("Title missing");
    if (!product?.currentPrice || product?.currentPrice <= 0) failureReason.push("Price missing/invalid");
    console.log(`(${context}) ❌ Scrape failed. Reasons: [${failureReason.join(', ')}]. lastSuccessfullyScrapedTitle remains: "${lastSuccessfullyScrapedTitle}"`);
  }
}

/**
 * Scrapes the Myntra product page. Returns the product object or null.
 */
function scrapeMyntra() {
    console.log("🔍 Starting scrapeMyntra function...");
    
    const title = document.querySelector('h1.pdp-title')?.innerText.trim() || '';
    if (title) console.log(`[scrapeMyntra] Found title: "${title}"`);

    const priceText = document.querySelector('span.pdp-price')?.innerText.trim() || '';
    if (priceText) console.log(`[scrapeMyntra] Found price text: "${priceText}"`);

    let imageUrl = '';
    const imageEl = document.querySelector('.image-grid-image');
    if (imageEl) {
        const style_attr = imageEl.style.backgroundImage;
        if (style_attr && style_attr.includes('url("')) {
            imageUrl = style_attr.split('url("')[1].split('")')[0];
            if (imageUrl) console.log(`[scrapeMyntra] Found image URL from style`);
        }
    }
    
    // Add description scraping
    const description = document.querySelector('.pdp-product-description-content')?.innerText.trim() || '';
    if (description) console.log(`[scrapeMyntra] Found description`);
    
    // Add brand scraping
    const brand = document.querySelector('h1.pdp-name')?.innerText.trim() || '';
    if (brand) console.log(`[scrapeMyntra] Found brand: "${brand}"`);

    const result = {
        title: title,
        currentPrice: normalizePrice(priceText),
        imageUrl: imageUrl,
        brand: brand,
        description: description,
        source: "Myntra"
    };
    console.log("[scrapeMyntra] Finished scraping. Raw result:", result);
    return result;
}

/**
 * Waits for the product title AND price to appear and title to change,
 * then scrapes and sends data immediately.
 */
function waitForContentAndScrape(context) {
  // Prevent multiple simultaneous attempts
  if (scrapeAttemptedForCurrentNavigation) {
      console.log(`[waitForContentAndScrape / ${context}] Scrape already attempted/running for this navigation. Skipping.`);
      return;
  }
  scrapeAttemptedForCurrentNavigation = true; // Set flag early
  hasSentInfoForThisScrape = false; // Reset send flag for this new attempt

  const titleSelector = "h1.pdp-title"; // Myntra's title
  const priceSelectors = ['span.pdp-price']; // Myntra's price
  const checkInterval = 250;
  const maxWait = 5000;
  let waited = 0;

  console.log(`[waitForContentAndScrape / ${context}] Starting poll. Last successfully scraped title: "${lastSuccessfullyScrapedTitle}"`);

  const interval = setInterval(() => {
    // Stop if another scrape finished in the meantime
    if (hasSentInfoForThisScrape) {
         console.log(`[waitForContentAndScrape / ${context}] Scrape completed by another trigger. Stopping poll.`);
        clearInterval(interval);
        return;
    }

    const currentTitleElement = document.querySelector(titleSelector);
    const currentTitle = currentTitleElement ? currentTitleElement.innerText.trim() : "";
    
    let currentPriceElement = null;
    for(const pSelector of priceSelectors){
        currentPriceElement = document.querySelector(pSelector);
        if(currentPriceElement) break;
    }

    // Condition: We found a title, we found a price, AND
    // the title is not empty, AND
    // the title is DIFFERENT from the last one we scraped.
    const conditionMet = currentTitleElement && 
                         currentPriceElement && 
                         currentTitle && 
                         currentTitle !== lastSuccessfullyScrapedTitle;

    if (conditionMet) {
      clearInterval(interval);
      console.log(`[waitForContentAndScrape / ${context}] Detected new title AND price. New title: "${currentTitle}". Scraping immediately...`);
      // *** SCRAPE IMMEDIATELY ***
      const productData = scrapeMyntra();
      sendProductInfo(productData, context + " / Content Change Detected");
    } else {
      waited += checkInterval;
      if (waited >= maxWait) {
        console.warn(`[waitForContentAndScrape / ${context}] Timeout waiting for new product title/price change. Running scrape anyway.`);
        clearInterval(interval);
        
        // *** SCRAPE AFTER TIMEOUT ***
        const productData = scrapeMyntra();
        if (productData.title && productData.title !== lastSuccessfullyScrapedTitle) {
             sendProductInfo(productData, context + " / Wait Timeout");
        } else if (!lastSuccessfullyScrapedTitle && productData.title) {
             sendProductInfo(productData, context + " / Wait Timeout (First Load)");
        } else {
             console.log(`[waitForContentAndScrape / ${context}] Timeout scrape found same title or no title. Not sending.`);
             if (!productData.title) {
                sendProductInfo(null, context + " / Wait Timeout (Scrape Failed)");
             }
        }
      }
    }
  }, checkInterval);
}

// --- Main Execution & Listener for Background Message ---

// Run the wait & scrape sequence on initial load
console.log(`Initial page load. Last title: "${lastSuccessfullyScrapedTitle}"`);
scrapeAttemptedForCurrentNavigation = false; // Reset flag for initial load
waitForContentAndScrape("Initial Load");


// Listen ONLY for messages from our background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Check that the message is from our extension, not a webpage
  if (sender.id !== chrome.runtime.id) {
    return false;
  }
    
  if (message.type === "RUN_SCRAPE") {
    console.log(" Received RUN_SCRAPE message from background. Resetting flag and starting wait...");
    // This is the key: a navigation happened. Reset the attempt flag.
    scrapeAttemptedForCurrentNavigation = false;
    waitForContentAndScrape("Background Trigger");
    sendResponse({ success: true }); // Acknowledge the message
  }
  return true; // Indicate you may respond asynchronously
});

console.log("Myntra content script loaded and listener attached.");