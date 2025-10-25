// extension/scrapers/flipkart.js
console.log("--- FLIPKART SCRAPER v12.2 (Better Polling) IS RUNNING ---");

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
 * Scrapes the Flipkart product page. Returns the product object or null.
 */
function scrapeFlipkart() {
    console.log("🔍 Starting scrapeFlipkart function...");
    let title = '';
    const titleSelectors = ['span.VU-ZEz', 'span.B_NuCI'];
    for (const selector of titleSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            title = el.innerText.trim();
            console.log(`[scrapeFlipkart] Found title text: "${title}"`);
            break;
        }
    }

    let priceText = '';
    const priceSelectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj'];
    for (const selector of priceSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            priceText = el.innerText.trim();
            console.log(`[scrapeFlipkart] Found price text using selector "${selector}": ${priceText}`);
            break;
        }
    }

    let imageUrl = '';
    const imageSelectors = ['img.DByuf4', 'img._396cs4._2amPTt._3qGmMb', 'img._2r_T1E', 'img.q6DClP'];
     for (const selector of imageSelectors) {
        const el = document.querySelector(selector);
         if (el) {
             imageUrl = el.getAttribute('src');
             if (imageUrl && imageUrl.startsWith('http')) {
                 console.log(`[scrapeFlipkart] Found image URL using selector "${selector}"`);
                 break;
             } else { imageUrl = ''; }
         }
     }

    let description = '';
    const descriptionSelectors = [
        'div.Xbd0Sd p', 
        '._1mXcCf.RmoJUa p', 
        'div._1AN87F' // Bullet points
    ];
     for (const selector of descriptionSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            if (selector === 'div._1AN87F') {
                 const listItems = Array.from(el.querySelectorAll('li._21Ahn-'));
                 description = listItems.map(li => `• ${li.innerText.trim()}`).join('\n');
            } else {
                description = el.innerText.trim();
            }
            if (description) {
                 console.log(`[scrapeFlipkart] Found description using selector "${selector}"`);
                 break;
            }
        }
    }

    const result = {
        title,
        currentPrice: normalizePrice(priceText),
        imageUrl,
        brand: '', // Brand is tricky on Flipkart
        description,
        source: "Flipkart"
    };
    console.log("[scrapeFlipkart] Finished scraping. Raw result:", result);
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

  const titleSelector = "span.VU-ZEz, span.B_NuCI";
  // --- THIS IS THE FIX ---
  // Added all known price selectors to the poll
  const priceSelectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj'];
  // --- END OF FIX ---
  
  const checkInterval = 250;
  const maxWait = 7000; // 7 seconds
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
    const conditionMet = currentTitleElement && 
                         currentPriceElement && 
                         currentTitle && 
                         currentTitle !== lastSuccessfullyScrapedTitle;

    if (conditionMet) {
      clearInterval(interval);
      console.log(`[waitForContentAndScrape / ${context}] Detected new title AND price. New title: "${currentTitle}". Scraping immediately...`);
      // *** SCRAPE IMMEDIATELY ***
      const productData = scrapeFlipkart();
      sendProductInfo(productData, context + " / Content Change Detected");
    } else {
      waited += checkInterval;
      if (waited >= maxWait) {
        console.warn(`[waitForContentAndScrape / ${context}] Timeout waiting for new product title/price change. Running scrape anyway.`);
        clearInterval(interval);
        
        // *** SCRAPE AFTER TIMEOUT ***
        const productData = scrapeFlipkart();
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

console.log("Flipkart content script loaded and listener attached.");