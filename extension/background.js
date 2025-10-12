let currentProductInfo = null;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "PRODUCT_INFO") {
        currentProductInfo = request.product;
        // No response needed, just storing the data
        return;
    }
    
    if (request.type === "GET_PRODUCT_INFO") {
        sendResponse(currentProductInfo);
        return;
    }
    
    if (request.type === "TRACK_PRODUCT") {
        // INSTEAD of sender.tab.url, we query for the active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length === 0) {
                sendResponse({ success: false, message: "Could not find active tab." });
                return;
            }
            const activeTab = tabs[0];
            const productUrl = activeTab.url;

            fetch('http://localhost:8000/api/products/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: productUrl,
                    title: request.product.title,
                }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
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
        
        // Return true because we will respond asynchronously
        return true;
    }
});