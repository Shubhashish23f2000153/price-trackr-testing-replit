import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getProduct,
  getPriceHistory,
  addToWatchlist,
  removeFromWatchlist,
  deleteProduct,
  getWatchlist,
  getScamScore,
  ProductDetail as ProductDetailType,
  PriceHistoryItem,
  Watchlist,
  ScamScore
} from '../services/api';
// --- Import Icons ---
import { ArrowLeft, Tag, BarChart2, Heart, Trash2, AlertTriangle, Star, CheckCircle, HelpCircle } from 'lucide-react';
// --- End Import ---
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';
import TrustBadge from '../components/TrustBadge';

// --- Seller Trust Helper Functions & Component ---
interface SellerTrustInfo {
  level: 'good' | 'okay' | 'poor' | 'new' | 'unknown';
  message: string;
}

// Function to parse rating string (e.g., "4.5 Stars", "90% Positive") into a number 0-5
const parseRating = (ratingStr: string | null | undefined): number | null => {
    if (!ratingStr) return null;
    let numericRating: number | null = null;

    // Check for "X.X Stars" or just "X.X"
    let match = ratingStr.match(/([\d\.]+)/);
    if (match) {
        numericRating = parseFloat(match[1]);
    } else {
        // Check for "XX% Positive"
        match = ratingStr.match(/(\d+)%\s*Positive/i);
        if (match) {
            // Convert percentage to a 0-5 scale (simple linear mapping)
            numericRating = (parseFloat(match[1]) / 100) * 5;
        }
    }
    // Clamp rating between 0 and 5
    if (numericRating !== null) {
       return Math.max(0, Math.min(5, numericRating));
    }
    return null;
};

// Function to parse review count string (e.g., "1,500", "5k") into a number
const parseReviewCount = (countStr: string | null | undefined): number | null => {
    if (!countStr) return null;
    let numStr = countStr.toLowerCase().replace(/,/g, '');
    let multiplier = 1;
    if (numStr.endsWith('k')) {
        multiplier = 1000;
        numStr = numStr.slice(0, -1);
    } else if (numStr.endsWith('m')) {
        multiplier = 1000000;
        numStr = numStr.slice(0, -1);
    }
    const num = parseFloat(numStr);
    return isNaN(num) ? null : Math.round(num * multiplier);
};

// Determines seller trust level based on rating and review count
const getSellerTrustLevel = (
    ratingStr: string | null | undefined,
    countStr: string | null | undefined
): SellerTrustInfo => {
    const rating = parseRating(ratingStr);
    const count = parseReviewCount(countStr);

    if (rating === null && (count === null || count === 0)) {
        return { level: 'unknown', message: 'Seller information not available.' };
    }

    // Prioritize low rating regardless of count
    if (rating !== null && rating < 3.5) {
        return { level: 'poor', message: `Low seller rating (${rating.toFixed(1)}/5). Consider checking recent reviews.` };
    }

    // High rating and high count = good
    if (rating !== null && rating >= 4.2 && count !== null && count >= 500) {
        return { level: 'good', message: `Good rating (${rating.toFixed(1)}/5) with many reviews (${count.toLocaleString()}).` };
    }

    // Good rating but low count = new/unproven
    if (rating !== null && rating >= 4.0 && (count === null || count < 100)) {
        return { level: 'new', message: `Rating is okay (${rating.toFixed(1)}/5), but seller has few reviews. Verify seller reputation.` };
    }
     // Only count available, and it's low
    if (rating === null && count !== null && count < 100) {
        return { level: 'new', message: `Seller has few reviews (${count.toLocaleString()}). Verify seller reputation.` };
    }

    // Default to 'okay' for moderate ratings or high counts with moderate ratings
    if (rating !== null || count !== null) {
        let message = "Seller rating seems acceptable.";
        if (rating !== null) message += ` (${rating.toFixed(1)}/5)`;
        if (count !== null) message += ` (${count.toLocaleString()} reviews)`;
        return { level: 'okay', message: message };
    }

    return { level: 'unknown', message: 'Could not determine seller trust.' }; // Fallback
};

// Component to display the seller trust level with icon and hover info
const SellerTrustIndicator: React.FC<{ trustInfo: SellerTrustInfo }> = ({ trustInfo }) => {
    const details = {
        good: { Icon: CheckCircle, color: 'text-green-600 dark:text-green-400', text: 'Good Seller Rating' },
        okay: { Icon: CheckCircle, color: 'text-blue-600 dark:text-blue-400', text: 'Okay Seller Rating' },
        new: { Icon: HelpCircle, color: 'text-yellow-600 dark:text-yellow-400', text: 'New/Few Reviews' },
        poor: { Icon: AlertTriangle, color: 'text-red-600 dark:text-red-400', text: 'Low Seller Rating' },
        unknown: { Icon: HelpCircle, color: 'text-gray-500 dark:text-gray-400', text: 'Seller Info Unknown' }
    }[trustInfo.level];

    const [isPopoverVisible, setIsPopoverVisible] = useState(false);

    // Don't render if level is unknown and message indicates unavailability
    if (trustInfo.level === 'unknown' && trustInfo.message === 'Seller information not available.') {
      return null;
    }


    return (
        <div className={`relative flex items-center space-x-1 text-xs ${details.color}`}>
            <details.Icon className="w-3.5 h-3.5 flex-shrink-0" /> {/* Added flex-shrink-0 */}
            <span
                className="cursor-help whitespace-nowrap" // Added whitespace-nowrap
                onMouseEnter={() => setIsPopoverVisible(true)}
                onMouseLeave={() => setIsPopoverVisible(false)}
            >
                {details.text}
            </span>
            {isPopoverVisible && (
                <div className="absolute top-full left-0 mt-1 w-60 p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow-lg z-10 text-xs text-gray-700 dark:text-gray-300">
                    {trustInfo.message}
                </div>
            )}
        </div>
    );
};
// --- End Seller Trust ---


// Helper function to extract domain (remains the same)
const getDomainFromUrl = (url: string): string | null => {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.hostname.replace('www.', '');
  } catch (error) {
    console.warn("Could not parse URL for domain:", url);
    return null;
  }
};

// Helper function to find watchlist item ID (remains the same)
const findWatchlistItemId = (productId: number | undefined, watchlist: Watchlist[]): number | null => {
    if (productId === undefined) return null;
    const item = watchlist.find(w => w.product_id === productId);
    return item ? item.id : null;
};

// --- Main Component ---
export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();
  // State Variables
  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [history, setHistory] = useState<PriceHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isWatchlisted, setIsWatchlisted] = useState(false);
  const [userWatchlist, setUserWatchlist] = useState<Watchlist[]>([]);
  const { lastMessage } = useWebSocket();
  const numProductId = parseInt(productId || "0");
  const { user } = useAuth();
  const [scamScore, setScamScore] = useState<ScamScore | null>(null);
  const [isScamScoreLoading, setIsScamScoreLoading] = useState(true);

  // Live update WebSocket Effect
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'PRICE_UPDATE' && lastMessage.product_id === numProductId) {
      console.log("Live update received!", lastMessage);
      setProduct(prevProduct => {
        if (!prevProduct) return null;

        const updatedPrices = prevProduct.prices.map(priceInfo => {
          if (priceInfo.source_name.toLowerCase() === lastMessage.source_name.toLowerCase()) {
            return {
                ...priceInfo,
                current_price: lastMessage.new_price,
                // Update seller info if present in WS message
                seller_name: lastMessage.seller_name !== undefined ? lastMessage.seller_name : priceInfo.seller_name,
                seller_rating: lastMessage.seller_rating !== undefined ? lastMessage.seller_rating : priceInfo.seller_rating,
                seller_review_count: lastMessage.seller_review_count !== undefined ? lastMessage.seller_review_count : priceInfo.seller_review_count,
            };
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
                currency: "INR", // Defaults, adjust if needed
                availability: "In Stock",
                in_stock: true,
                url: "", // Not available in WS
                seller_name: lastMessage.seller_name,
                seller_rating: lastMessage.seller_rating,
                seller_review_count: lastMessage.seller_review_count,
            });
        }

        const newLowest = Math.min(
          prevProduct.lowest_ever_price || Infinity,
          lastMessage.new_price
        );

        return { ...prevProduct, prices: updatedPrices, lowest_ever_price: newLowest };
      });
    }
  }, [lastMessage, numProductId]);

  // Data Fetching Effect
  useEffect(() => {
    if (!productId) { setIsLoading(false); return; }
    const numProductId = parseInt(productId);
    if (isNaN(numProductId)) { setIsLoading(false); setProduct(null); return; }

    const fetchAllData = async () => {
      setIsLoading(true);
      setIsScamScoreLoading(true);
      setProduct(null);
      setScamScore(null);
      setHistory([]); // Clear history too

      try {
        // Fetch product and history
        const productPromise = getProduct(numProductId);
        const historyPromise = getPriceHistory(numProductId);
        const [productData, historyData] = await Promise.all([productPromise, historyPromise]);

        setProduct(productData);
        setHistory(historyData.map((h: PriceHistoryItem) => ({
            ...h,
            date: new Date(h.date).toLocaleDateString()
        })));

        // Fetch watchlist
        setIsWatchlisted(productData.is_in_watchlist); // Set initial
        try {
            const watchlistData = await getWatchlist();
            setUserWatchlist(watchlistData);
            const watchlistItem = watchlistData.find(item => item.product_id === numProductId);
            setIsWatchlisted(!!watchlistItem); // Update with actual
        } catch (watchlistError) {
            console.warn("Could not fetch watchlist, using product default.", watchlistError);
        }

        // Fetch Domain Scam Score
        let domainToCheck: string | null = null;
        if (productData.prices.length > 0 && productData.prices[0].url) {
            domainToCheck = getDomainFromUrl(productData.prices[0].url);
        }

        if (domainToCheck) {
            try {
                const scoreData = await getScamScore(domainToCheck);
                setScamScore(scoreData);
            } catch (scamError) {
                console.error("Failed to fetch scam score:", scamError);
                setScamScore(null);
            } finally {
                 setIsScamScoreLoading(false);
            }
        } else {
            setIsScamScoreLoading(false); // No domain, finish loading
        }

      } catch (error) {
        console.error("Failed to fetch essential product details:", error);
        setProduct(null);
        setIsScamScoreLoading(false); // Ensure loading stops on error
      } finally {
        setIsLoading(false);
      }
    };
    fetchAllData();
  }, [productId]); // Re-run ALL fetches if the productId changes


  // Event Handlers
  const handleToggleWatchlist = async () => {
    if (!product) return;

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

  // Loading and Error States
  if (isLoading) {
    return <div className="text-center p-8">Loading product details...</div>;
  }
  if (!product) {
    return <div className="text-center p-8 card bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">Product not found or failed to load.</div>;
  }

  // Determine latest price for overview card (simple check)
  const latestPriceInfoForOverview = product.prices.length > 0 ? product.prices[0] : null;

  // Render JSX
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

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column (Image & Prices) */}
        <div className="md:col-span-1 space-y-4">
          <div className="card p-4 flex justify-center items-center aspect-square">
            <img src={product.image_url || 'https://via.placeholder.com/300?text=No+Image'} alt={product.title} className="rounded-lg object-contain w-full h-full max-h-80" />
          </div>
          <div className="card">
             <h3 className="text-lg font-semibold mb-4 flex items-center"><Tag className="w-5 h-5 mr-2" /> Current Prices</h3>
             <div className="space-y-4">
               {product.prices.length > 0 ? product.prices.map(price => {
                   const sellerTrustInfo = getSellerTrustLevel(price.seller_rating, price.seller_review_count);
                   return (
                     <div key={`${price.source_name}-${price.url}`} className="pb-3 border-b border-gray-100 dark:border-gray-800 last:border-b-0 last:pb-0">
                       <div className="flex justify-between items-center gap-2 mb-1">
                         <a href={price.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm truncate flex-1 font-medium" title={price.source_name}>{price.source_name}</a>
                         <span className="font-bold text-lg whitespace-nowrap">₹{price.current_price.toLocaleString()}</span>
                       </div>
                       {(price.seller_name || price.seller_rating || sellerTrustInfo.level !== 'unknown') && (
                         <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                            {price.seller_name && <div>Sold by: {price.seller_name}</div>}
                            <div className="flex items-center space-x-2 flex-wrap">
                                {price.seller_rating && (
                                <span className="flex items-center space-x-1">
                                    <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                                    <span>{price.seller_rating}</span>
                                    {/* Make sure seller_review_count is treated as string before toLocaleString */}
                                    {price.seller_review_count && <span>({parseReviewCount(price.seller_review_count)?.toLocaleString() ?? price.seller_review_count})</span>}
                                </span>
                                )}
                                <SellerTrustIndicator trustInfo={sellerTrustInfo} />
                           </div>
                         </div>
                       )}
                     </div>
                   );
               }) : <p className="text-sm text-gray-500">No current price information available.</p>}
             </div>
             {/* Domain Trust Badge */}
             <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <TrustBadge scoreData={scamScore} isLoading={isScamScoreLoading} />
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
                  ₹{product.lowest_ever_price?.toLocaleString() || (latestPriceInfoForOverview ? latestPriceInfoForOverview.current_price.toLocaleString() : 'N/A')}
                </span>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center"><BarChart2 className="w-5 h-5 mr-2" /> Price History (Last 30 Days)</h3>
            {history.length > 1 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb dark:stroke-gray-700" />
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

      {/* Danger Zone */}
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