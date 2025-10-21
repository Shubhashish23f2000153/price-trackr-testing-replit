let currentProductInfo = null;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "PRODUCT_INFO") {
        currentProductInfo = request.product;
        return; // No response needed
    }
    
    if (request.type === "GET_PRODUCT_INFO") {
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
});