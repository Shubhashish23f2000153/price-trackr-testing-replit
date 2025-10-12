document.addEventListener('DOMContentLoaded', () => {
    const loadingMessage = document.getElementById('loading-message');
    const productTitleEl = document.getElementById('product-title');
    const productPriceEl = document.getElementById('product-price');
    const trackButton = document.getElementById('track-button');
    const statusMessage = document.getElementById('status-message');

    let productData = null;

    // Ask the background script for the product info
    chrome.runtime.sendMessage({ type: "GET_PRODUCT_INFO" }, (product) => {
        loadingMessage.classList.add('hidden');
        
        if (product) {
            productData = product;
            productTitleEl.textContent = product.title;
            productPriceEl.textContent = product.price;

            productTitleEl.classList.remove('hidden');
            productPriceEl.classList.remove('hidden');
            trackButton.classList.remove('hidden');
        } else {
            loadingMessage.textContent = "No product found on this page.";
            loadingMessage.classList.remove('hidden');
        }
    });

    // Handle the track button click
    trackButton.addEventListener('click', () => {
        if (!productData) return;
        
        trackButton.disabled = true;
        trackButton.textContent = 'Tracking...';

        chrome.runtime.sendMessage({ type: "TRACK_PRODUCT", product: productData }, (response) => {
            if (response.success) {
                statusMessage.textContent = response.message;
                statusMessage.style.color = 'green';
                trackButton.style.display = 'none';
            } else {
                statusMessage.textContent = response.message;
                statusMessage.style.color = 'red';
                trackButton.disabled = false;
                trackButton.textContent = 'Track This Product';
            }
        });
    });
});