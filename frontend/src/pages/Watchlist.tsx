import { useState, useEffect } from 'react';
import { Heart, ExternalLink } from 'lucide-react';
import { getWatchlist, getProduct, ProductDetail } from '../services/api';
import { Link } from 'react-router-dom';

export default function Watchlist() {
  const [watchlistItems, setWatchlistItems] = useState<ProductDetail[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchWatchlistData = async () => {
      try {
        const watchlist = await getWatchlist();
        const productPromises = watchlist.map(item => getProduct(item.product_id));
        const detailedProducts = await Promise.all(productPromises);
        setWatchlistItems(detailedProducts);
      } catch (error) {
        console.error("Failed to fetch watchlist data:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWatchlistData();
  }, []);

  if (isLoading) {
    return <div className="text-center p-8">Loading watchlist...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Watchlist</h2>
        <p className="text-gray-600 dark:text-gray-400">Items you've starred and are tracking in your queue</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Total Products</span>
          <div className="text-3xl font-bold mt-1">{watchlistItems.length}</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Price Drops</span>
          <div className="text-3xl font-bold mt-1">N/A</div>
        </div>
        <div className="card">
          <span className="text-sm text-gray-600 dark:text-gray-400">Potential Savings</span>
          <div className="text-3xl font-bold mt-1">N/A</div>
        </div>
      </div>

      <div className="space-y-4">
        {watchlistItems.length > 0 ? (
          watchlistItems.map((item) => {
            const priceInfo = item.prices[0];
            return (
              <div key={item.id} className="card flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-start space-x-3">
                    <Heart className="w-5 h-5 text-red-500 fill-red-500 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-medium mb-2">{item.title}</h3>
                      <div className="flex items-center space-x-6 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Source: </span>
                          <span className="font-medium">{priceInfo?.source_name || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Current Price: </span>
                          <span className="font-bold">₹{priceInfo?.current_price.toLocaleString() || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Status: </span>
                          <span className="text-green-600 dark:text-green-400">{priceInfo?.availability || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Link to={`/product/${item.id}`} className="btn-secondary text-sm flex items-center space-x-1">
                    <span>View Details</span>
                  </Link>
                  <button className="btn-primary text-sm flex items-center space-x-1">
                    <ExternalLink className="w-4 h-4" />
                    <span>Set Alert</span>
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="card text-center py-8">
            <p className="text-gray-500">Your watchlist is empty.</p>
            <p className="text-sm text-gray-400 mt-2">Add products to start tracking their prices.</p>
          </div>
        )}
      </div>
    </div>
  );
}