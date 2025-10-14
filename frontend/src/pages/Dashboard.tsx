import { useEffect, useState } from 'react';
import { TrendingDown, TrendingUp, Package, DollarSign } from 'lucide-react';
import { getProducts, getDashboardStats, Product } from '../services/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_products: 0,
    total_saved: 0,
    active_deals: 0,
    price_drops: 0
  });
  const [recentActivity, setRecentActivity] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch stats and recent products in parallel
        const statsPromise = getDashboardStats();
        const productsPromise = getProducts();
        
        const [statsData, products] = await Promise.all([statsPromise, productsPromise]);
        
        setStats(statsData);

        const sortedProducts = [...products].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setRecentActivity(sortedProducts.slice(0, 3));

      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return <div className="text-center p-8">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Dashboard</h2>
        <p className="text-gray-600 dark:text-gray-400">Welcome! Here's what's happening with your tracked items today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Total Products Tracked</span>
            <Package className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold">{stats.total_products}</div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Potential Savings</span>
            <DollarSign className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold">₹{stats.total_saved.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Active Deals</span>
            <TrendingDown className="w-5 h-5 text-orange-500" />
          </div>
          <div className="text-3xl font-bold">{stats.active_deals}</div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">Price Drops Today</span>
            <TrendingUp className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-3xl font-bold">{stats.price_drops}</div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recently Tracked Products</h3>
          <Link to="/watchlist" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">View All</Link>
        </div>
        <div className="space-y-4">
          {recentActivity.length > 0 ? (
            recentActivity.map((item) => (
              <div key={item.id} className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-sm mb-1">{item.title}</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                    Tracked on: {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Link to={`/product/${item.id}`} className="btn-primary text-sm">
                  View Details
                </Link>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500">No recent activity. Add a product to get started!</p>
          )}
        </div>
      </div>
    </div>
  );
}