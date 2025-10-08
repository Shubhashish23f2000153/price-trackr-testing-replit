import { useState } from 'react'
import { Tag, Calendar } from 'lucide-react'

export default function Sales() {
  const [activeTab, setActiveTab] = useState('ongoing')
  const [stats] = useState({
    activeSales: 4,
    upcomingSales: 2,
    topDeals: 4,
    avgDiscount: 54
  })

  const sales = [
    {
      id: 1,
      title: "Diwali Mega Sale",
      description: "Up to 80% off across all electronics",
      discount: 80,
      source: "Amazon",
      endDate: "2025-11-15"
    },
    {
      id: 2,
      title: "Black Friday Sale",
      description: "Extra 20% off",
      discount: 20,
      source: "Flipkart",
      endDate: "2025-11-30"
    },
    {
      id: 3,
      title: "End of Season Sale",
      description: "Flat 50-80% off",
      discount: 65,
      source: "Myntra",
      endDate: "2025-12-10"
    },
    {
      id: 4,
      title: "Weekend Sale",
      description: "Extra 20% off",
      discount: 20,
      source: "Amazon",
      endDate: "2025-10-12"
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Sales & Deals</h2>
        <p className="text-gray-600 dark:text-gray-400">Track upcoming sales and promotional deals across platforms</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Active Sales</span>
          <div className="text-3xl font-bold mt-1">{stats.activeSales}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Upcoming Sales</span>
          <div className="text-3xl font-bold mt-1">{stats.upcomingSales}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Top Deals</span>
          <div className="text-3xl font-bold mt-1">{stats.topDeals}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Avg. Discount</span>
          <div className="text-3xl font-bold mt-1">{stats.avgDiscount}%</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={() => setActiveTab('ongoing')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'ongoing'
              ? 'border-black dark:border-white text-gray-900 dark:text-white'
              : 'border-transparent text-gray-600 dark:text-gray-400'
          }`}
        >
          Ongoing
        </button>
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'upcoming'
              ? 'border-black dark:border-white text-gray-900 dark:text-white'
              : 'border-transparent text-gray-600 dark:text-gray-400'
          }`}
        >
          Upcoming
        </button>
      </div>

      {/* Sales Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sales.map((sale) => (
          <div key={sale.id} className="card">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Tag className="w-5 h-5 text-orange-500" />
                <span className="text-xs px-2 py-1 bg-black dark:bg-white text-white dark:text-black rounded font-medium">
                  {sale.source}
                </span>
              </div>
              <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                {sale.discount}%
              </span>
            </div>
            <h3 className="font-semibold text-lg mb-2">{sale.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {sale.description}
            </p>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Calendar className="w-4 h-4" />
                <span>Ends {sale.endDate}</span>
              </div>
              <button className="btn-primary text-sm">View Sale</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
