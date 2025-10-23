import { useState } from 'react';
import { Link2, CheckCircle, AlertCircle } from 'lucide-react';
import { trackProduct } from '../services/api';

export default function AddProduct() {
  const [productUrl, setProductUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productUrl) return;

    setIsLoading(true);
    setMessage(null);
    
    try {
      // This function sends the URL to your backend's /api/products/track endpoint
      await trackProduct(productUrl);
      setMessage({ type: 'success', text: 'Product added successfully! Scraping will begin shortly.' });
      setProductUrl(''); // Clear the input field on success
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to add product. Please try again.';
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const suggestedSites = [
    { name: "Amazon India", domain: "amazon.in", supported: true },
    { name: "Flipkart", domain: "flipkart.com", supported: true },
    { name: "Myntra", domain: "myntra.com", supported: true },
    { name: "Snapdeal", domain: "snapdeal.com", supported: true },
    { name: "Meesho", domain: "meesho.com", supported: true }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Add Product</h2>
        <p className="text-gray-600 dark:text-gray-400">Enter a product link from any supported e-commerce site.</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {message && (
            <div className={`p-4 rounded-lg flex items-center space-x-2 ${
              message.type === 'success' 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300' 
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
            }`}>
              {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
              <span>{message.text}</span>
            </div>
          )}
          <div>
            <label htmlFor="productUrl" className="block text-sm font-medium mb-2">Product URL</label>
            {/* THIS IS THE CORRECTED LINE */}
            <div className="relative">
              <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="productUrl"
                type="url"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                placeholder="https://www.amazon.in/product/..."
                className="input pl-10"
                required
                disabled={isLoading}
              />
            </div>
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isLoading}>
            {isLoading ? 'Adding Product...' : 'Track Product'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Supported Sites</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Our scrapers currently support the following e-commerce platforms.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {suggestedSites.map((site) => (
            <div
              key={site.domain}
              className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">{site.name}</div>
                  <div className="text-xs text-gray-500">{site.domain}</div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  site.supported
                    ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}>
                  {site.supported ? 'Supported' : 'Coming Soon'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}