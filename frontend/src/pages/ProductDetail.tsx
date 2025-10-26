import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getProduct,
  getPriceHistory,
  addToWatchlist,
  removeFromWatchlist,
  deleteProduct,
  getWatchlist,
  ProductDetail as ProductDetailType,
  PriceHistoryItem,
  Watchlist
} from '../services/api';
import { ArrowLeft, Tag, BarChart2, Heart, Trash2, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext'; // 1. Import useAuth

// Helper function
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
  const [userWatchlist, setUserWatchlist] = useState<Watchlist[]>([]);
  const { lastMessage } = useWebSocket();
  const numProductId = parseInt(productId || "0");
  const { user } = useAuth(); // 2. Get the user state

  // Live update WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'PRICE_UPDATE' && lastMessage.product_id === numProductId) {
      console.log("Live update received!", lastMessage);
      setProduct(prevProduct => {
        if (!prevProduct) return null;
        
        const updatedPrices = prevProduct.prices.map(priceInfo => {
          if (priceInfo.source_name.toLowerCase() === lastMessage.source_name.toLowerCase()) {
            return { ...priceInfo, current_price: lastMessage.new_price };
          }
          return priceInfo;
        });
        
        const sourceExists = prevProduct.prices.some(
          p => p.source_name.toLowerCase() === lastMessage.source_name.toLowerCase()
        );

        if (!sourceExists) {
            updatedPrices.push({
                source_name: lastMessage.source_name,
                current_price: lastMessage.new_price,
                currency: "INR", 
                availability: "In Stock", 
                in_stock: true, 
                url: "" 
            });
        }

        const newLowest = Math.min(
          prevProduct.lowest_ever_price || Infinity,
          lastMessage.new_price
        );
        
        return {
          ...prevProduct,
          prices: updatedPrices,
          lowest_ever_price: newLowest,
        };
      });
    }
  }, [lastMessage, numProductId]);

  // Modified Data Fetching
  useEffect(() => {
    if (!productId) {
        setIsLoading(false);
        return;
    }
    const numProductId = parseInt(productId);
    if (isNaN(numProductId)) {
        setIsLoading(false);
        setProduct(null);
        return;
    }

    const fetchEssentialData = async () => {
      setIsLoading(true);
      try {
        // 1. Fetch essential data first
        const productPromise = getProduct(numProductId);
        const historyPromise = getPriceHistory(numProductId);
        
        const [productData, historyData] = await Promise.all([
          productPromise,
          historyPromise
        ]);

        setProduct(productData);
        setHistory(historyData.map((h: PriceHistoryItem) => ({
            ...h,
            date: new Date(h.date).toLocaleDateString()
        })));
        
        // 2. Fetch non-essential data (watchlist) separately
        setIsWatchlisted(productData.is_in_watchlist);
        try {
            const watchlistData = await getWatchlist();
            setUserWatchlist(watchlistData); 
            const watchlistItem = watchlistData.find(item => item.product_id === numProductId);
            setIsWatchlisted(!!watchlistItem); // Update with the most current info
        } catch (watchlistError) {
            console.warn("Could not fetch watchlist, using product default.", watchlistError);
        }

      } catch (error) {
        console.error("Failed to fetch essential product details:", error);
        setProduct(null); 
      } finally {
        setIsLoading(false);
      }
    };
    fetchEssentialData();
  }, [productId]);


  const handleToggleWatchlist = async () => {
    if (!product) return;

    // 3. Prompt user to login if they are a guest
    if (!user) {
      if (window.confirm("You need to be logged in to save items to your watchlist.\n\nClick OK to go to the login page.")) {
        navigate('/login');
      }
      return;
    }

    const currentProductId = product.id;
    try {
      if (isWatchlisted) {
        const watchlistItemIdToRemove = findWatchlistItemId(currentProductId, userWatchlist);
        if (watchlistItemIdToRemove !== null) {
          await removeFromWatchlist(watchlistItemIdToRemove);
          setUserWatchlist(prev => prev.filter(item => item.id !== watchlistItemIdToRemove));
          setIsWatchlisted(false);
        } else {
           console.error("Could not find watchlist item ID to remove.");
           alert("Error: Could not find item in watchlist to remove.");
           return;
        }
      } else {
        const newItem = await addToWatchlist(currentProductId);
        setUserWatchlist(prev => [...prev, newItem]);
        setIsWatchlisted(true);
      }
    } catch (error) {
      console.error("Failed to update watchlist:", error);
      alert("Failed to update watchlist status.");
    }
  };

  const handleDelete = async () => {
     if (product && window.confirm("Are you sure? This will permanently delete the product and all its price history.")) {
      try {
        await deleteProduct(product.id);
        navigate('/');
      } catch (error) {
        console.error("Failed to delete product:", error);
        alert("Failed to delete product.");
      }
    }
  };

  if (isLoading) {
    return <div className="text-center p-8">Loading product details...</div>;
  }
  if (!product) {
    return <div className="text-center p-8 card bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">Product not found or failed to load.</div>;
  }

  const latestPriceInfo = product.prices.length > 0 ? product.prices[product.prices.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <Link to="/all-products" className="flex items-center space-x-2 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to All Products</span>
          </Link>
          <h2 className="text-2xl md:text-3xl font-bold break-words">{product.title}</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Brand: {product.brand || 'N/A'}</p>
        </div>
        <button
          onClick={handleToggleWatchlist}
          title={isWatchlisted ? "Remove from Watchlist" : "Add to Watchlist"}
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0 mt-12 md:mt-16"
        >
          <Heart className={`w-7 h-7 md:w-8 md:h-8 transition-all ${isWatchlisted ? 'text-red-500 fill-red-500' : 'text-gray-400 hover:text-red-300'}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column (Image & Prices) */}
        <div className="md:col-span-1 space-y-4">
          <div className="card p-4 flex justify-center items-center aspect-square">
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

        {/* Right Column (Chart & Details) */}
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
            {history.length > 1 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" /> 
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

      {/* Danger Zone -- THIS IS THE FIX --- */}
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