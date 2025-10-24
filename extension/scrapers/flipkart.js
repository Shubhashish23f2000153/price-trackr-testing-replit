// This is the debug message to check if the new script is loading.
console.log("--- FLIPKART SCRAPER v11 (description fix) IS RUNNING ---");

/**
 * Normalizes a price string by removing currency symbols and commas.
 * @param {string} priceStr The price string to normalize.
 * @returns {number} The normalized price as a number.
 */
function normalizePrice(priceStr) {
    if (!priceStr) return 0;
    const cleaned = priceStr.replace(/[₹,MRP\s]/g, '').trim();
    const price = parseFloat(cleaned);
    return isNaN(price) ? 0 : price;
}

/**
 * Sends a message from the content script to other parts of the extension.
 * @param {object | null} product The product data to send, or null.
 */
function sendProductInfo(product) {
  if (product && product.title && product.currentPrice > 0) {
    console.log("✅ Found product:", product);
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: product });
  } else {
    // Log detailed failure reason if possible
    let failureReason = [];
    if (!product?.title) failureReason.push("Title missing");
    if (!product?.currentPrice || product.currentPrice <= 0) failureReason.push("Price missing/invalid");
    console.log(`❌ Failed to find valid product details. Reasons: [${failureReason.join(', ')}]. Title:`, product?.title, "Price:", product?.currentPrice);
    chrome.runtime.sendMessage({ type: "PRODUCT_INFO", product: null });
  }
}

/**
 * Scrapes the Flipkart product page.
 */
function scrapeFlipkart() {
    console.log("🔍 Starting scrapeFlipkart function...");
    let title = '';
    const titleSelectors = ['span.VU-ZEz', 'span.B_NuCI'];
    for (const selector of titleSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            title = el.innerText.trim();
            console.log(`✅ Found title using selector "${selector}":`, title);
            break;
        } else {
             console.log(`❌ Title selector "${selector}" did not match.`);
        }
    }
    if (!title) console.log("❌ Could not find title using any selector.");

    let priceText = '';
    const priceSelectors = ['div._30jeq3', 'div._1vC4OE', 'div.h10eU > div:first-child', 'div.Nx9bqj'];
    for (const selector of priceSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            priceText = el.innerText.trim();
            console.log(`✅ Found price text using selector "${selector}":`, priceText);
            break;
        } else {
            console.log(`❌ Price selector "${selector}" did not match.`);
        }
    }
     if (!priceText) console.log("❌ Could not find price text using any selector.");

    let imageUrl = '';
    const imageSelectors = ['img.DByuf4', 'img._396cs4._2amPTt._3qGmMb', 'img._2r_T1E', 'img.q6DClP'];
     for (const selector of imageSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            imageUrl = el.getAttribute('src');
             if (imageUrl && imageUrl.startsWith('http')) {
                 console.log(`✅ Found image URL using selector "${selector}"`);
                 break;
             } else {
                  console.log(`⚠️ Found image element with selector "${selector}", but 'src' is missing or invalid: ${imageUrl}`);
                  imageUrl = '';
             }
        } else {
             console.log(`❌ Image selector "${selector}" did not match.`);
        }
    }
    if (!imageUrl) console.log("❌ Could not find image URL using any selector.");

    // --- UPDATED DESCRIPTION SELECTOR ---
    let description = '';
    const descriptionSelectors = [
        'div.Xbd0Sd p', // From image_3fd30b.png
        '._1mXcCf.RmoJUa p', // Old selector as fallback
        'div._1AN87F' // Common selector for bullet points (might need further processing)
    ];
     for (const selector of descriptionSelectors) {
        const el = document.querySelector(selector);
        if (el) {
            // If it's the bullet point div, grab all list items
            if (selector === 'div._1AN87F') {
                 const listItems = Array.from(el.querySelectorAll('li._21Ahn-'));
                 description = listItems.map(li => `• ${li.innerText.trim()}`).join('\n');
            } else {
                description = el.innerText.trim();
            }

            if (description) {
                 console.log(`✅ Found description using selector "${selector}"`);
                 break;
            }
        } else {
             console.log(`❌ Description selector "${selector}" did not match.`);
        }
    }
    if (!description) console.log("❌ Could not find description using any selector.");
    // --- END OF DESCRIPTION UPDATE ---

    return {
        title,
        currentPrice: normalizePrice(priceText),
        imageUrl,
        brand: '', // Brand still needs a reliable selector
        description,
        source: "Flipkart"
    };
}

// --- Main execution ---
sendProductInfo(scrapeFlipkart());