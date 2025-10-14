document.addEventListener('DOMContentLoaded', () => {
    const loadingMessage = document.getElementById('loading-message');
    const productTitleEl = document.getElementById('product-title');
    const productPriceEl = document.getElementById('product-price');
    const productDetailsContainer = document.getElementById('product-details');
    const trackButton = document.getElementById('track-button');
    const statusMessage = document.getElementById('status-message');

    let productData = null;

    chrome.runtime.sendMessage({ type: "GET_PRODUCT_INFO" }, (product) => {
        loadingMessage.classList.add('hidden');
        
        if (product) {
            productData = product;
            productTitleEl.textContent = product.title;
            productPriceEl.textContent = product.price;

            productDetailsContainer.classList.remove('hidden');
            trackButton.classList.remove('hidden');
        } else {
            loadingMessage.textContent = "No supported product found on this page.";
            loadingMessage.classList.remove('hidden');
        }
    });

    trackButton.addEventListener('click', () => {
        if (!productData) return;
        
        trackButton.disabled = true;
        trackButton.textContent = 'Tracking...';

        chrome.runtime.sendMessage({ type: "TRACK_PRODUCT", product: productData }, (response) => {
            statusMessage.textContent = response.message;
            statusMessage.classList.remove('hidden');

            if (response.success) {
                statusMessage.classList.add('status-success');
                trackButton.classList.add('hidden');
            } else {
                statusMessage.classList.add('status-error');
                trackButton.disabled = false;
                trackButton.textContent = 'Track This Product';
            }
        });
    });
});