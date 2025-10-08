import { useState } from 'react'
import { Heart, ExternalLink } from 'lucide-react'

export default function Watchlist() {
  const [watchlistItems] = useState([
    {
      id: 1,
      product: "Sony WH-1000XM5 Wireless Industry Leading Noise Canceling Headphones",
      source: "Amazon",
      price: 24990,
      currency: "INR",
      availability: "In Stock"
    },
    {
      id: 2,
      product: "Apple iPhone 14 Pro (256GB) - Natural Titanium",
      source: "Flipkart",
      price: 119900,
      currency: "INR",
      availability: "In Stock"
    },
    {
      id: 3,
      product: "Samsung Galaxy S25 Ultra 5G (Titanium Black, 12GB, 256GB Storage)",
      source: "Amazon",
      price: 120999,
      currency: "INR",
      availability: "In Stock"
    },
    {
      id: 4,
      product: "Xiaomi 120 Watt, 30 Wireless Performance",
      source: "Flipkart",
      price: 6995,
      currency: "INR",
      availability: "In Stock"
    }
  ])

  const [stats] = useState({
    totalProducts: 6,
    priceDrops: 3,
    avgDiscount: 12499
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Watchlist</h2>
        <p className="text-gray-600 dark:text-gray-400">Items you've starred and are tracking in your queue</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Total Product</span>
          <div className="text-3xl font-bold mt-1">{stats.totalProducts}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Price Drops</span>
          <div className="text-3xl font-bold mt-1">{stats.priceDrops}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Discount Average</span>
          <div className="text-3xl font-bold mt-1">₹{stats.avgDiscount.toLocaleString()}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <button className="btn-secondary text-sm">Price (High)</button>
        <button className="btn-secondary text-sm">Availability</button>
        <button className="btn-secondary text-sm">NEWEST</button>
      </div>

      {/* Watchlist Items */}
      <div className="space-y-4">
        {watchlistItems.map((item) => (
          <div key={item.id} className="card flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-start space-x-3">
                <Heart className="w-5 h-5 text-red-500 fill-red-500 mt-1" />
                <div className="flex-1">
                  <h3 className="font-medium mb-2">{item.product}</h3>
                  <div className="flex items-center space-x-6 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Source: </span>
                      <span className="font-medium">{item.source}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Current Price: </span>
                      <span className="font-bold">₹{item.price.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Status: </span>
                      <span className="text-green-600 dark:text-green-400">{item.availability}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex space-x-2">
              <button className="btn-secondary text-sm flex items-center space-x-1">
                <span>View Deal</span>
              </button>
              <button className="btn-primary text-sm flex items-center space-x-1">
                <ExternalLink className="w-4 h-4" />
                <span>Get Alert</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
