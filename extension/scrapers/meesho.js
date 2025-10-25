// Debug message to check if script is running
console.log("--- MEESHO SCRAPER v12 (Hybrid Polling) IS RUNNING ---");

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
 * Scrapes the Meesho product page. Returns the product object or null.
 */
function scrapeMeesho() {
    console.log("🔍 Starting scrapeMeesho function...");
    
    let title = '';
    const titleSelectors = ['h1']; // Main product title
    for (const selector of titleSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            title = el.innerText.trim();
             console.log(`[scrapeMeesho] Found title text: "${title}"`);
             break;
        } else {
             console.log(`[scrapeMeesho] Title selector "${selector}" failed.`);
        }
    }

    let priceTextRaw = '';
    let priceTextNum = '';
    const priceSelectors = ['h4', 'h4.sc-eDV5Ve', 'h4[class*="Price__PriceValue"]'];
    for (const selector of priceSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            priceTextRaw = el.innerText.trim();
            const priceMatch = priceTextRaw.match(/₹?([\d,]+)/);
            if (priceMatch && priceMatch[1]) {
                 priceTextNum = priceMatch[1];
                 console.log(`[scrapeMeesho] Found price text using selector "${selector}": ${priceTextRaw} -> Extracted: ${priceTextNum}`);
                 break;
            } else {
                 console.log(`[scrapeMeesho] Price selector "${selector}" matched, but couldn't extract number from: ${priceTextRaw}`);
            }
        } else {
             console.log(`[scrapeMeesho] Price selector "${selector}" failed.`);
        }
    }

    let imageUrl = '';
    const imageSelectors = ['img.AviImage_ImageWrapper-sc-1055enk-0', 'div[class*="ProductDesktopImage"] img', 'picture img'];
    for (const selector of imageSelectors) {
        const el = document.querySelector(selector);
         if (el) {
             imageUrl = el.getAttribute('src');
             if (imageUrl && imageUrl.startsWith('http')) {
                 console.log(`[scrapeMeesho] Found image URL using selector "${selector}"`);
                 break;
             } else { imageUrl = ''; }
         } else {
              console.log(`[scrapeMeesho] Image selector "${selector}" failed.`);
         }
     }

    let description = '';
    const descriptionSelectors = ['div[class*="ProductDescription__DescriptionContainer"]', 'div.content'];
    for (const selector of descriptionSelectors) {
        const el = document.querySelector(selector);
         if (el) { description = el.innerText.trim(); if (description) { console.log(`[scrapeMeesho] Found description using selector "${selector}"`); break;} }
         else { console.log(`[scrapeMeesho] Description selector "${selector}" failed.`);}
     }

    const result = {
        title,
        currentPrice: normalizePrice(priceTextNum),
        imageUrl,
        brand: '',
        description,
        source: "Meesho"
    };
    console.log("[scrapeMeesho] Finished scraping. Raw result:", result);
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

  const titleSelector = "h1";
  const priceSelectors = ['h4', 'h4.sc-eDV5Ve', 'h4[class*="Price__PriceValue"]'];
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

    // *** THE KEY LOGIC ***
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
      const productData = scrapeMeesho();
      sendProductInfo(productData, context + " / Content Change Detected");
    } else {
      waited += checkInterval;
      if (waited >= maxWait) {
        console.warn(`[waitForContentAndScrape / ${context}] Timeout waiting for new product title/price change. Running scrape anyway.`);
        clearInterval(interval);
        
        // *** SCRAPE AFTER TIMEOUT ***
        // This handles the very first page load, where lastSuccessfullyScrapedTitle is ""
        const productData = scrapeMeesho();
        if (productData.title && productData.title !== lastSuccessfullyScrapedTitle) {
             // This case happens if the page was just slow to load
             sendProductInfo(productData, context + " / Wait Timeout");
        } else if (!lastSuccessfullyScrapedTitle && productData.title) {
             // If this is the first ever scrape and it timed out, send it anyway
             sendProductInfo(productData, context + " / Wait Timeout (First Load)");
        } else {
             console.log(`[waitForContentAndScrape / ${context}] Timeout scrape found same title or no title. Not sending.`);
             // Send null to clear any old data in popup if scrape failed
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

console.log("Meesho content script loaded and listener attached.");