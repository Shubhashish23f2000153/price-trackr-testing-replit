import { useEffect, useState } from 'react'
import { TrendingDown, TrendingUp, Package, DollarSign } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalProducts: 247,
    totalSaved: 2147,
    activeDeals: 18,
    priceDrops: 42
  })

  const [recentActivity, setRecentActivity] = useState([
    {
      id: 1,
      product: "Sony WH-1000XM5 Wireless Industry Leading Noise Canceling Headphones",
      source: "Amazon",
      price: 24990,
      oldPrice: 29990,
      date: "5/12/2025, 11:42AM - Manual Tracked"
    },
    {
      id: 2,
      product: "Apple iPhone 14 Pro (256GB) - Natural Titanium",
      source: "Flipkart",
      price: 119900,
      oldPrice: 129900,
      date: "3/15/2025"
    },
    {
      id: 3,
      product: "Samsung Galaxy S25 Ultra 5G (Titanium Black, 12GB, 256GB Storage)",
      source: "Amazon",
      price: 120999,
      oldPrice: 134999,
      date: "4/18/2025"
    }
  ])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Dashboard</h2>
        <p className="text-gray-600 dark:text-gray-400">Welcome! Here's what's happening with your tracked items today</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Total Product</span>
            <Package className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold">{stats.totalProducts}</div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">You Saved</span>
            <DollarSign className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold">₹{stats.totalSaved.toLocaleString()}</div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Active Deals</span>
            <TrendingDown className="w-5 h-5 text-orange-500" />
          </div>
          <div className="text-3xl font-bold">{stats.activeDeals}</div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Price Drops</span>
            <TrendingUp className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-3xl font-bold">{stats.priceDrops}</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Active Price Alerts</h3>
          <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">View All</button>
        </div>
        <div className="space-y-4">
          {recentActivity.map((item) => {
            const discount = ((item.oldPrice - item.price) / item.oldPrice * 100).toFixed(0)
            return (
              <div key={item.id} className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-sm mb-1">{item.product}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{item.date}</p>
                  <div className="flex items-center space-x-4">
                    <div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">Current Price</span>
                      <p className="text-lg font-bold">₹{item.price.toLocaleString()}</p>
                    </div>
                    <div className="text-green-600 dark:text-green-400 text-sm font-medium">
                      ↓ {discount}% off
                    </div>
                  </div>
                </div>
                <button className="btn-primary text-sm">View Deal</button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
