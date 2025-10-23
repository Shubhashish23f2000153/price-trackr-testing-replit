// frontend/src/pages/AllProducts.tsx
import { useState, useEffect } from 'react';
import { getProducts, Product } from '../services/api';
import { Link } from 'react-router-dom';
import { List } from 'lucide-react'; // Example Icon

export default function AllProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const productData = await getProducts(0, 500); // Fetch a large number
        setProducts(productData);
      } catch (error) {
        console.error("Failed to fetch all products:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProducts();
  }, []);

  if (isLoading) {
    return <div className="text-center p-8">Loading all tracked products...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <List className="w-6 h-6" />
        <h2 className="text-2xl font-semibold">All Tracked Products ({products.length})</h2>
      </div>
      
      {products.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((product) => (
            <div key={product.id} className="card p-4 flex flex-col justify-between">
              <div>
                <img src={product.image_url || 'https://via.placeholder.com/150'} alt={product.title} className="rounded-md object-contain h-40 w-full mb-3" />
                <h3 className="font-medium text-sm mb-1 line-clamp-2">{product.title}</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  Tracked on: {new Date(product.created_at).toLocaleDateString()}
                </p>
              </div>
              <Link to={`/product/${product.id}`} className="btn-secondary text-sm mt-3 w-full text-center">
                View Details
              </Link>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-8">
          <p className="text-gray-500">No products have been tracked yet.</p>
        </div>
      )}
    </div>
  );
}