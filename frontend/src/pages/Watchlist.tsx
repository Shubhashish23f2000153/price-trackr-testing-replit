import { useState, useEffect } from 'react';
import { Heart, ExternalLink } from 'lucide-react';
import { getWatchlist, getProduct, updateWatchlistAlert, ProductDetail, Watchlist as WatchlistType } from '../services/api';
import { Link } from 'react-router-dom';
import SetAlertModal from '../components/modals/SetAlertModal';

export default function Watchlist() {
  const [watchlistItems, setWatchlistItems] = useState<ProductDetail[]>([]);
  const [rawWatchlist, setRawWatchlist] = useState<WatchlistType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductDetail | null>(null);

  const fetchWatchlistData = async () => {
    try {
      // Don't set loading to true on refetch
      // setIsLoading(true); 
      const watchlist = await getWatchlist();
      setRawWatchlist(watchlist);
      if (watchlist.length > 0) {
        const productPromises = watchlist.map(item => getProduct(item.product_id));
        const detailedProducts = await Promise.all(productPromises);
        setWatchlistItems(detailedProducts);
      } else {
        setWatchlistItems([]);
      }
    } catch (error) {
      console.error("Failed to fetch watchlist data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    fetchWatchlistData();
  }, []);

  const handleOpenModal = (product: ProductDetail) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setSelectedProduct(null);
    setIsModalOpen(false);
  };

  const handleSaveAlert = async (price: number) => {
    if (!selectedProduct) return;
    
    const watchlistItem = rawWatchlist.find(item => item.product_id === selectedProduct.id);
    if (!watchlistItem) return;

    setIsSaving(true);
    try {
      await updateWatchlistAlert(watchlistItem.id, price);
      await fetchWatchlistData(); // Refetch data to show updated alert info
    } catch (error) {
      console.error("Failed to save alert:", error);
    } finally {
      setIsSaving(false);
      handleCloseModal();
    }
  };

  if (isLoading) {
    return <div className="text-center p-8">Loading watchlist...</div>;
  }

  return (
    <>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold mb-2">Watchlist</h2>
          <p className="text-gray-600 dark:text-gray-400">Items you've starred and are tracking in your queue</p>
        </div>

        <div className="space-y-4">
          {watchlistItems.length > 0 ? (
            watchlistItems.map((item) => {
              const priceInfo = item.prices[0];
              const watchlistItem = rawWatchlist.find(w => w.product_id === item.id);
              const alertPrice = watchlistItem?.alert_rules?.threshold;

              return (
                <div key={item.id} className="card flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-start space-x-3">
                      <Heart className="w-5 h-5 text-red-500 fill-red-500 mt-1 flex-shrink-0" />
                      <div className="flex-1">
                        <h3 className="font-medium mb-2">{item.title}</h3>
                        <div className="flex items-center space-x-6 text-sm mb-2">
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Source: </span>
                                <span className="font-medium">{priceInfo?.source_name || 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Current Price: </span>
                                <span className="font-bold">₹{priceInfo?.current_price.toLocaleString() || 'N/A'}</span>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-500 mt-2">
                          {alertPrice ? (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">
                              Alert set for price below ₹{alertPrice.toLocaleString()}
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 rounded">
                              No alert set
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col md:flex-row items-end md:items-center space-y-2 md:space-y-0 md:space-x-2">
                    <Link to={`/product/${item.id}`} className="btn-secondary text-sm">View Details</Link>
                    <button onClick={() => handleOpenModal(item)} className="btn-primary text-sm flex items-center space-x-1">
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

      {isModalOpen && selectedProduct && (
        <SetAlertModal
          productTitle={selectedProduct.title}
          currentPrice={selectedProduct.prices[0]?.current_price || 0}
          onClose={handleCloseModal}
          onSave={handleSaveAlert}
          isLoading={isSaving}
        />
      )}
    </>
  );
}