import { useState, useEffect } from 'react';
import { Tag, Calendar } from 'lucide-react';
import { getSales, Sale } from '../services/api'; // Import the API function and type

export default function Sales() {
  const [ongoingSales, setOngoingSales] = useState<Sale[]>([]);
  const [upcomingSales, setUpcomingSales] = useState<Sale[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ongoing');

  useEffect(() => {
    const fetchSalesData = async () => {
      try {
        // Fetch both ongoing and upcoming sales in parallel
        const ongoingPromise = getSales(undefined, 'ongoing');
        const upcomingPromise = getSales(undefined, 'upcoming');
        
        const [ongoingData, upcomingData] = await Promise.all([ongoingPromise, upcomingPromise]);
        
        setOngoingSales(ongoingData);
        setUpcomingSales(upcomingData);
      } catch (error) {
        console.error("Failed to fetch sales data:", error);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSalesData();
  }, []);

  const salesToDisplay = activeTab === 'ongoing' ? ongoingSales : upcomingSales;

  if (isLoading) {
    return <div>Loading sales data...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Sales & Deals</h2>
        <p className="text-gray-600 dark:text-gray-400">Track upcoming sales and promotional deals across platforms.</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 border-b border-gray-200 dark:border-gray-800">
        <button
          onClick={() => setActiveTab('ongoing')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'ongoing'
              ? 'border-black dark:border-white text-gray-900 dark:text-white'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Ongoing ({ongoingSales.length})
        </button>
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'upcoming'
              ? 'border-black dark:border-white text-gray-900 dark:text-white'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Upcoming ({upcomingSales.length})
        </button>
      </div>

      {/* Sales Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {salesToDisplay.length > 0 ? (
          salesToDisplay.map((sale) => (
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
                  <span>
                    {activeTab === 'ongoing' ? 'Ends' : 'Starts'}: {sale.end_date ? new Date(sale.end_date).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
                <button className="btn-primary text-sm">View Sale</button>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-1 md:col-span-2 card text-center py-8">
            <p className="text-gray-500">No {activeTab} sales found at the moment.</p>
          </div>
        )}
      </div>
    </div>
  );
}