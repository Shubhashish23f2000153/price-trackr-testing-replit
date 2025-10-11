import { useState, useEffect } from 'react'
import { Tag, Calendar } from 'lucide-react'
import { getSales, Sale } from '../services/api' // Import the API function and type

export default function Sales() {
  const [sales, setSales] = useState<Sale[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('ongoing')

  useEffect(() => {
    const fetchSales = async () => {
      try {
        const salesData = await getSales()
        setSales(salesData)
      } catch (error) {
        console.error("Failed to fetch sales:", error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchSales()
  }, [])

  if (isLoading) {
    return <div>Loading sales data...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Sales & Deals</h2>
        <p className="text-gray-600 dark:text-gray-400">Track upcoming sales and promotional deals across platforms</p>
      </div>

      {/* You can add back the stats and tabs here if you wish */}

      {/* Sales Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sales.length > 0 ? (
          sales.map((sale) => (
            <div key={sale.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Tag className="w-5 h-5 text-orange-500" />
                  <span className="text-xs px-2 py-1 bg-black dark:bg-white text-white dark:text-black rounded font-medium">
                    {sale.source_domain}
                  </span>
                </div>
                {sale.discount_percentage && (
                   <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {sale.discount_percentage}%
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-lg mb-2">{sale.title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {sale.description}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Calendar className="w-4 h-4" />
                  {/* You might want to format this date nicely */}
                  <span>Ends {sale.end_date ? new Date(sale.end_date).toLocaleDateString() : 'N/A'}</span>
                </div>
                <button className="btn-primary text-sm">View Sale</button>
              </div>
            </div>
          ))
        ) : (
          <p>No sales data found. You can add some via the API.</p>
        )}
      </div>
    </div>
  )
}