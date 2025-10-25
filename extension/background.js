// extension/background.js
let currentProductInfo = null; 

// List of all supported domains from your manifest
const supportedDomains = [
    "amazon.in",
    "flipkart.com",
    "myntra.com",
    "snapdeal.com",
    "meesho.com"
];

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Check if the URL is one we support
    const isSupported = tab.url && supportedDomains.some(domain => tab.url.includes(domain));
    if (!isSupported) {
        return;
    }

    // We only trigger a scrape, we DO NOT reset the data here.
    // The content script is responsible for sending new data (or null).
    if (changeInfo.url || changeInfo.status === 'complete') {
        
        if (changeInfo.url) {
            console.log(`[Background] URL changed in tab ${tabId}. Sending RUN_SCRAPE.`);
        }
        if (changeInfo.status === 'complete') {
            console.log(`[Background] Tab ${tabId} finished loading. Sending RUN_SCRAPE.`);
        }

        // --- BUG FIX ---
        // The line "currentProductInfo = null;" has been REMOVED from here.
        // --- END BUG FIX ---
        
        // Send the message to the content script in that tab
        chrome.tabs.sendMessage(tabId, { type: "RUN_SCRAPE" }, (response) => {
            if (chrome.runtime.lastError) {
                // This is normal if the content script isn't injected yet,
                // it will run its own "Initial Load" scrape anyway.
                // console.log("Content script not ready yet, or no receiver.");
            } else {
                // console.log(`[Background] Content script in tab ${tabId} acknowledged RUN_SCRAPE.`);
            }
        });
    }
});


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "PRODUCT_INFO") {
        // This is the ONLY place currentProductInfo should be set.
        currentProductInfo = request.product; 
        console.log("[Background] Received PRODUCT_INFO. Data is now:", currentProductInfo);
        return; // No response needed
    }
    
    if (request.type === "GET_PRODUCT_INFO") {
        console.log("[Background] Popup requested data. Sending:", currentProductInfo);
        sendResponse(currentProductInfo);
        return; // Respond immediately
    }
    
    if (request.type === "TRACK_PRODUCT") {
        // Use the correct, modern way to get the active tab's URL
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (!tabs.length || !tabs[0].url) {
                sendResponse({ success: false, message: "Could not find the active tab's URL." });
                return;
            }
            const productUrl = tabs[0].url;

            // Send the full data package to the new endpoint
            fetch('http://localhost:8000/api/products/add-from-extension', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...request.product, url: productUrl }),
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                sendResponse({ success: true, message: "Product is now being tracked!" });
            })
            .catch(error => {
                console.error('Error tracking product:', error);
                sendResponse({ success: false, message: "Error: Could not connect to the backend." });
            });
        });
        
        // This is crucial: return true to indicate you will respond asynchronously
        return true;
    }
    return true; // Keep this true for async message handling
});