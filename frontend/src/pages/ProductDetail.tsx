import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getProduct,
  getPriceHistory,
  addToWatchlist,
  removeFromWatchlist, // Ensure this is imported correctly
  deleteProduct,
  getWatchlist, // Import getWatchlist
  ProductDetail as ProductDetailType,
  PriceHistoryItem,
  Watchlist
} from '../services/api';
import { ArrowLeft, Tag, BarChart2, Heart, Trash2, AlertTriangle } from 'lucide-react'; // Added AlertTriangle
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Helper function to find the specific watchlist item ID
const findWatchlistItemId = (productId: number | undefined, watchlist: Watchlist[]): number | null => {
    if (productId === undefined) return null;
    const item = watchlist.find(w => w.product_id === productId);
    return item ? item.id : null;
};

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [history, setHistory] = useState<PriceHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isWatchlisted, setIsWatchlisted] = useState(false);
  const [userWatchlist, setUserWatchlist] = useState<Watchlist[]>([]); // State to hold the raw watchlist

  useEffect(() => {
    if (!productId) {
        setIsLoading(false); // Stop loading if no ID
        return;
    }
    const numProductId = parseInt(productId);
    if (isNaN(numProductId)) {
        setIsLoading(false); // Stop loading if ID is not a number
        setProduct(null); // Ensure product is null if ID invalid
        return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch product details and watchlist in parallel
        const productPromise = getProduct(numProductId);
        const historyPromise = getPriceHistory(numProductId);
        const watchlistPromise = getWatchlist(); // Fetch the user's watchlist

        const [productData, historyData, watchlistData] = await Promise.all([
          productPromise,
          historyPromise,
          watchlistPromise
        ]);

        setProduct(productData);
        setUserWatchlist(watchlistData); // Store the raw watchlist

        // Check if the current product is in the fetched watchlist
        const watchlistItem = watchlistData.find(item => item.product_id === numProductId);
        // Use the backend is_in_watchlist flag *if available*, otherwise check manually
        setIsWatchlisted(productData.is_in_watchlist ?? !!watchlistItem);

        setHistory(historyData.map((h: PriceHistoryItem) => ({
            ...h,
            date: new Date(h.date).toLocaleDateString()
        })));

      } catch (error) {
        console.error("Failed to fetch product details or watchlist:", error);
        setProduct(null); // Set product to null on error to show 'not found'
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [productId]); // Re-run effect if productId changes

  // ** FULLY IMPLEMENTED handleToggleWatchlist function **
  const handleToggleWatchlist = async () => {
    if (!product) return;
    const currentProductId = product.id; // Store ID

    try {
      if (isWatchlisted) {
        // Find the specific ID of the watchlist item to remove
        const watchlistItemIdToRemove = findWatchlistItemId(currentProductId, userWatchlist);

        if (watchlistItemIdToRemove !== null) {
          await removeFromWatchlist(watchlistItemIdToRemove); // Call the API function
          // Update local state after successful removal
          setUserWatchlist(prev => prev.filter(item => item.id !== watchlistItemIdToRemove));
          setIsWatchlisted(false);
        } else {
           console.error("Could not find watchlist item ID to remove. User watchlist:", userWatchlist);
           alert("Error: Could not find item in watchlist to remove. Maybe refresh?");
           // We might not want to toggle state if the backend call fails conceptually
           // setIsWatchlisted(false); // Only toggle on success
           return; // Stop if ID wasn't found
        }
      } else {
        // Add to watchlist
        const newItem = await addToWatchlist(currentProductId);
        // Update local state after successful addition
        setUserWatchlist(prev => [...prev, newItem]);
        setIsWatchlisted(true);
      }
    } catch (error) {
      console.error("Failed to update watchlist:", error);
      alert("Failed to update watchlist status. Please try again.");
      // Potentially revert UI state toggle on error here
    }
  };

  // handleDelete function remains the same...
  const handleDelete = async () => {
     if (product && window.confirm("Are you sure? This will permanently delete the product and all its price history.")) {
      try {
        await deleteProduct(product.id);
        navigate('/'); // Redirect to dashboard
      } catch (error) {
        console.error("Failed to delete product:", error);
        alert("Failed to delete product.");
      }
    }
  };


  // Loading and Not Found states
  if (isLoading) {
    return <div className="text-center p-8">Loading product details...</div>;
  }
  if (!product) {
    return <div className="text-center p-8 card bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">Product not found or failed to load. It might have been deleted or the ID is invalid.</div>;
  }

  // Find the most recent price info
  const latestPriceInfo = product.prices.length > 0 ? product.prices[product.prices.length - 1] : null;


  // ** FULL JSX **
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        {/* Left Side: Back Link, Title, Brand */}
        <div className="flex-1 min-w-0"> {/* Added min-w-0 for better wrapping */}
          <Link to="/all-products" className="flex items-center space-x-2 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to All Products</span>
          </Link>
          <h2 className="text-2xl md:text-3xl font-bold break-words">{product.title}</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Brand: {product.brand || 'N/A'}</p>
        </div>
        {/* Right Side: Watchlist Button */}
        <button
          onClick={handleToggleWatchlist}
          title={isWatchlisted ? "Remove from Watchlist" : "Add to Watchlist"}
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0 mt-12 md:mt-16" // Adjusted margin
        >
          <Heart className={`w-7 h-7 md:w-8 md:h-8 transition-all ${isWatchlisted ? 'text-red-500 fill-red-500' : 'text-gray-400 hover:text-red-300'}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Image & Current Prices */}
        <div className="md:col-span-1 space-y-4">
          <div className="card p-4 flex justify-center items-center aspect-square"> {/* Added aspect-square for consistency */}
            <img src={product.image_url || 'https://via.placeholder.com/300?text=No+Image'} alt={product.title} className="rounded-lg object-contain w-full h-full max-h-80" />
          </div>
          <div className="card">
             <h3 className="text-lg font-semibold mb-4 flex items-center"><Tag className="w-5 h-5 mr-2" /> Current Prices</h3>
             <div className="space-y-3">
               {product.prices.length > 0 ? product.prices.map(price => (
                 <div key={price.source_name} className="flex justify-between items-center gap-2">
                   <a href={price.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm truncate flex-1" title={price.source_name}>{price.source_name}</a>
                   <span className="font-bold text-lg whitespace-nowrap">₹{price.current_price.toLocaleString()}</span>
                 </div>
               )) : <p className="text-sm text-gray-500">No current price information available.</p>}
             </div>
          </div>
        </div>

        {/* Right Column: Overview, History, Description */}
        <div className="md:col-span-2 space-y-4">
          <div className="card">
            <h3 className="text-lg font-semibold mb-2">Price Overview</h3>
            <div className="flex items-baseline space-x-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-500">Lowest Ever (since tracking):</span>
                <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                  ₹{product.lowest_ever_price?.toLocaleString() || (latestPriceInfo ? latestPriceInfo.current_price.toLocaleString() : 'N/A')}
                </span>
            </div>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center"><BarChart2 className="w-5 h-5 mr-2" /> Price History (Last 30 Days)</h3>
            {history.length > 1 ? ( // Only show chart if there's more than one data point
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <YAxis domain={['dataMin - 100', 'dataMax + 100']} allowDecimals={false}/>
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="price" stroke="#8884d8" activeDot={{ r: 8 }} name="Price (₹)" />
                </LineChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-gray-500">Not enough price history available to display a chart yet (needs at least 2 price points).</p>}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">{product.description || 'No description available.'}</p>
          </div>
        </div>
      </div>

      {/* Danger Zone: Delete Button */}
      <div className="card border-red-500/30 dark:border-red-500/50 mt-8">
        <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5" />
          <span>Danger Zone</span>
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 mb-4">
          Permanently stop tracking this item. This action cannot be undone.
        </p>
        <button
          onClick={handleDelete}
          className="btn-secondary text-sm bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/40"
        >
          <Trash2 className="w-4 h-4 inline-block mr-2" />
          Stop Tracking Item
        </button>
      </div>
    </div>
  );
}