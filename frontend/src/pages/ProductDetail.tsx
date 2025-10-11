import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProduct, getPriceHistory, ProductDetail as ProductDetailType } from '../services/api';
import { ArrowLeft, Tag, BarChart2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!productId) return;

    const fetchData = async () => {
      try {
        const productData = await getProduct(parseInt(productId));
        const historyData = await getPriceHistory(parseInt(productId));
        setProduct(productData);
        // Format date for better chart display
        setHistory(historyData.map((h: any) => ({ ...h, date: new Date(h.date).toLocaleDateString() })));
      } catch (error) {
        console.error("Failed to fetch product details:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [productId]);

  if (isLoading) {
    return <div className="text-center p-8">Loading product details...</div>;
  }

  if (!product) {
    return <div className="text-center p-8">Product not found.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="flex items-center space-x-2 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-4">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
        <h2 className="text-3xl font-bold">{product.title}</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Brand: {product.brand || 'N/A'}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column for Image and Prices */}
        <div className="md:col-span-1 space-y-4">
          <div className="card p-4">
            <img src={product.image_url || 'https://via.placeholder.com/300'} alt={product.title} className="rounded-lg object-contain w-full h-auto" />
          </div>

          <div className="card">
             <h3 className="text-lg font-semibold mb-4 flex items-center"><Tag className="w-5 h-5 mr-2" /> Current Prices</h3>
             <div className="space-y-3">
               {product.prices.length > 0 ? product.prices.map(price => (
                 <div key={price.source_name} className="flex justify-between items-center">
                   <a href={price.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{price.source_name}</a>
                   <span className="font-bold text-lg">₹{price.current_price.toLocaleString()}</span>
                 </div>
               )) : <p className="text-sm text-gray-500">No price information available.</p>}
             </div>
          </div>
        </div>

        {/* Right Column for Details and Chart */}
        <div className="md:col-span-2 space-y-4">
          <div className="card">
            <h3 className="text-lg font-semibold mb-2">Price Overview</h3>
            <div className="flex items-baseline space-x-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-sm text-gray-500">Lowest Ever Price:</span>
                <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                  ₹{product.lowest_ever_price?.toLocaleString() || 'N/A'}
                </span>
            </div>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center"><BarChart2 className="w-5 h-5 mr-2" /> Price History (Last 30 Days)</h3>
            {history.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="price" stroke="#8884d8" activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-gray-500">No price history available to display a chart.</p>}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-2">Description</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{product.description || 'No description available.'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}