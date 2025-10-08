import { useState } from 'react'
import { Link2, Upload } from 'lucide-react'

export default function AddProduct() {
  const [productUrl, setProductUrl] = useState('')
  const [productFile, setProductFile] = useState<File | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Tracking product:', productUrl)
    // TODO: Implement API call
  }

  const suggestedSites = [
    { name: "Amazon India", domain: "amazon.in", supported: true },
    { name: "Flipkart", domain: "flipkart.com", supported: true },
    { name: "Myntra", domain: "myntra.com", supported: false },
    { name: "Snapdeal", domain: "snapdeal.com", supported: false },
    { name: "Meesho", domain: "meesho.com", supported: false }
  ]

  const tips = [
    "Make sure the product URL has been copied or screenshot e-commerce site.",
    "To get the URL, just copy..., we'll track the rest for you for free.",
    "Link availability will also show... will notify when available status of key.",
    "App is available on both [PWA app by clicking banner] in the home."
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Add Product</h2>
        <p className="text-gray-600 dark:text-gray-400">Enter product link from any supported e-commerce site</p>
      </div>

      {/* Add Product Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Product URL</label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Paste your product link from any supported e-commerce site
            </p>
            <div className="relative">
              <Link2 className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="url"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                placeholder="https://www.amazon.in/product/..."
                className="input pl-10"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Product File</label>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Or upload a screenshot
            </p>
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center">
              <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                Drag & drop or click to upload
              </p>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setProductFile(e.target.files?.[0] || null)}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="btn-secondary text-sm cursor-pointer inline-block">
                Choose File
              </label>
            </div>
          </div>

          <button type="submit" className="btn-primary w-full">
            Track Product
          </button>
        </form>
      </div>

      {/* Suggested Sites */}
      <div className="card">
        <h3 className="font-semibold mb-4">Suggested Sites</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Currently we are pulling prices & historic prices from e-commerce platforms
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {suggestedSites.map((site) => (
            <div
              key={site.domain}
              className={`p-3 rounded-lg border ${
                site.supported
                  ? 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                  : 'bg-gray-100 dark:bg-gray-900 border-gray-300 dark:border-gray-800'
              }`}
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

      {/* Tips */}
      <div className="card">
        <h3 className="font-semibold mb-4">💡 Quick Tips</h3>
        <ul className="space-y-2">
          {tips.map((tip, index) => (
            <li key={index} className="flex items-start space-x-2">
              <span className="w-1.5 h-1.5 bg-black dark:bg-white rounded-full mt-2"></span>
              <span className="text-sm text-gray-600 dark:text-gray-400">{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
