import { useState } from 'react';
import { X } from 'lucide-react';

interface SetAlertModalProps {
  productTitle: string;
  currentPrice: number;
  onClose: () => void;
  onSave: (price: number) => void;
  isLoading: boolean;
}

export default function SetAlertModal({ productTitle, currentPrice, onClose, onSave, isLoading }: SetAlertModalProps) {
  const [price, setPrice] = useState(currentPrice);

  const handleSave = () => {
    onSave(price);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg p-6 w-full max-w-md m-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Set Price Alert</h3>
          {/* ADDED aria-label HERE */}
          <button onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-black dark:hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          Set a price alert for: <span className="font-medium">{productTitle}</span>
        </p>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Current price is <span className="font-bold">₹{currentPrice.toLocaleString()}</span>. We'll notify you when the price drops below your target.
        </p>

        <div>
          <label htmlFor="price-input" className="block text-sm font-medium mb-2">Notify me when price is below:</label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">₹</span>
            <input
              id="price-input"
              type="number"
              value={price}
              onChange={(e) => setPrice(Number(e.target.value))}
              className="input pl-8"
            />
          </div>
        </div>
        
        <div className="mt-6 flex justify-end space-x-3">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave} className="btn-primary" disabled={isLoading}>
            {isLoading ? 'Saving...' : 'Save Alert'}
          </button>
        </div>
      </div>
    </div>
  );
}