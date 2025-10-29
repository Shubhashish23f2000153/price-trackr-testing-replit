import { useState, useEffect } from 'react';
import { Sun, Bell, Shield, Download, Trash2, AlertTriangle, MapPin, UserX } from 'lucide-react';
import { getSpaceStats, deleteAllProducts, getProducts, Product, deleteUser, getPriceHistory, PriceHistoryItem } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { countries } from '../utils/regionalData';
import { useAuth } from '../context/AuthContext';

// --- SettingsProps Interface ---
interface SettingsProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

// Interface for the combined export data structure
interface ProductWithHistory extends Product {
  price_history: PriceHistoryItem[];
}

// --- ToggleSwitchProps Interface ---
interface ToggleSwitchProps {
  label: string;
  description: string;
  enabled: boolean;
  setEnabled: (value: boolean) => void;
}

// --- CORRECTED ToggleSwitch Component ---
function ToggleSwitch({ label, description, enabled, setEnabled }: ToggleSwitchProps) {
  // The 'return' statement needs to be INSIDE the function body
  return (
    <div className="flex items-center justify-between">
      <div>
        <label className="font-medium">{label}</label>
        <div className="text-sm text-gray-500">{description}</div>
      </div>
      <button
        onClick={() => setEnabled(!enabled)}
        className={`flex items-center p-1 rounded-full w-12 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black dark:focus:ring-offset-gray-900 dark:focus:ring-white ${
          enabled ? 'bg-black dark:bg-white justify-end' : 'bg-gray-200 dark:bg-gray-700 justify-start'
        }`}
        aria-label={`Toggle ${label}`}
      >
        <span className={`block w-5 h-5 rounded-full shadow-lg transform ring-0 transition duration-200 ease-in-out ${
          enabled ? 'bg-white dark:bg-black' : 'bg-white dark:bg-gray-300'
        }`}/>
      </button>
    </div>
  );
} // <-- Added the missing closing brace


// --- Settings Component ---
export default function Settings({ darkMode, setDarkMode }: SettingsProps) {
  const [spaceInfo, setSpaceInfo] = useState({ tracked_items: 0, price_points: 0 });
  const navigate = useNavigate();
  const [country, setCountry] = useState(() => localStorage.getItem('userCountry') || 'IN');
  const [pushNotificationsEnabled, setPushNotificationsEnabled] = useState(() => localStorage.getItem('pushNotificationsEnabled') === 'false' ? false : true);
  const [priceDropAlertsEnabled, setPriceDropAlertsEnabled] = useState(() => localStorage.getItem('priceDropAlertsEnabled') === 'false' ? false : true);
  const [isExporting, setIsExporting] = useState(false);
  const { user, logout } = useAuth();

  // (All useEffect hooks remain the same)
  useEffect(() => { localStorage.setItem('userCountry', country); }, [country]);
  useEffect(() => { localStorage.setItem('pushNotificationsEnabled', String(pushNotificationsEnabled)); }, [pushNotificationsEnabled]);
  useEffect(() => { localStorage.setItem('priceDropAlertsEnabled', String(priceDropAlertsEnabled)); }, [priceDropAlertsEnabled]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const stats = await getSpaceStats();
        setSpaceInfo(stats);
      } catch (error) {
        console.error("Failed to fetch space info:", error);
      }
     };
    fetchStats();
  }, []);

  const handleClearAll = async () => {
     if (window.confirm("DANGER ZONE:\nAre you absolutely sure you want to delete ALL tracked products?\nThis action cannot be undone.")) {
      try {
        const result = await deleteAllProducts();
        alert(result.message);
        const updatedStats = await getSpaceStats();
        setSpaceInfo(updatedStats);
        navigate('/');
      } catch (error) {
        console.error("Failed to delete all products:", error);
        alert("Failed to delete all products. Please try again.");
      }
    }
   };

   const handleDeleteAccount = async () => {
    if (!user) {
      alert("You must be logged in to delete your account.");
      return;
    }
    if (window.confirm("DANGER ZONE:\nAre you absolutely sure you want to permanently delete your account and all associated data?\nThis action cannot be undone.")) {
      try {
        const result = await deleteUser();
        alert(result.message);
        logout();
        navigate('/login');
      } catch (error: any) {
        console.error("Failed to delete account:", error);
        const errorMessage = error.response?.data?.detail || "Failed to delete account. Please try again.";
        alert(errorMessage);
      }
    }
  };

  const handleExportData = async () => {
    setIsExporting(true);
    alert("Starting data export. This may take a while depending on the number of products tracked.");
    try {
      const allProducts: Product[] = await getProducts(0, 10000);
      if (!allProducts || allProducts.length === 0) {
        alert("No products found to export.");
        setIsExporting(false);
        return;
      }
      const productsWithHistory: ProductWithHistory[] = [];
      for (const product of allProducts) {
        try {
          const history = await getPriceHistory(product.id);
          productsWithHistory.push({ ...product, price_history: history });
        } catch (historyError) {
          console.error(`Failed to fetch history for product ${product.id}:`, historyError);
          productsWithHistory.push({ ...product, price_history: [] });
        }
      }
      const jsonData = JSON.stringify(productsWithHistory, null, 2);
      const blob = new Blob([jsonData], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `pricetrackr_export_full_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("Failed to export data:", error);
      alert("Failed to export data. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
       {/* (Header, Appearance, Region cards remain the same) ... */}
      <div>
        <h2 className="text-2xl font-semibold mb-2">Settings</h2>
        <p className="text-gray-600 dark:text-gray-400">Configure your price tracking preferences and notifications</p>
      </div>

      {/* Appearance Card */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Sun className="w-5 h-5" /><span>Appearance</span></h3>
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="theme-select" className="font-medium">Theme</label>
            <div className="text-sm text-gray-500">Choose your preferred theme</div>
          </div>
          <select id="theme-select" value={darkMode ? 'dark' : 'light'} onChange={(e) => setDarkMode(e.target.value === 'dark')} className="input w-32">
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>

      {/* Region & Currency Card */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><MapPin className="w-5 h-5" /><span>Region & Currency</span></h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="country-select" className="block text-sm font-medium mb-2">Default Region</label>
            <select
              id="country-select"
              className="input"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            >
              {countries.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label} ({c.currency})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>


      {/* Notifications Card - Uses ToggleSwitch */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Bell className="w-5 h-5" /><span>Notifications</span></h3>
        <div className="space-y-4">
          <ToggleSwitch
            label="Push Notifications"
            description="Receive browser notifications"
            enabled={pushNotificationsEnabled}
            setEnabled={setPushNotificationsEnabled}
          />
          <ToggleSwitch
            label="Price Drop Alerts"
            description="Notify when price drops below threshold"
            enabled={priceDropAlertsEnabled}
            setEnabled={setPriceDropAlertsEnabled}
          />
        </div>
      </div>

       {/* Privacy & Security Card */}
       <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Shield className="w-5 h-5" /><span>Privacy & Security</span></h3>
        <div className="space-y-4">
           <div>
             <h4 className="font-medium mb-1">Account Management</h4>
             <p className="text-sm text-gray-500 mb-3">Permanently delete your account and all associated data (watchlist, etc.). This cannot be undone.</p>
             <button
               onClick={handleDeleteAccount}
               disabled={!user}
               className="btn-secondary text-sm bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
             >
               <UserX className="w-4 h-4" />
               <span>Delete My Account</span>
             </button>
             {!user && <p className="text-xs text-red-600 mt-2">You must be logged in to delete your account.</p>}
           </div>
        </div>
      </div>

       {/* Space Information Card */}
       <div className="card">
        <h3 className="text-lg font-semibold mb-4">Space Information</h3>
        <div className="space-y-3">
           <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Tracked Items</span>
            <span className="font-medium">{spaceInfo.tracked_items} items</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Price Points Logged</span>
            <span className="font-medium">{spaceInfo.price_points} records</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Storage Used</span>
            <span className="font-medium">N/A</span>
          </div>
        </div>
        <button
          onClick={handleExportData}
          disabled={isExporting}
          className="btn-secondary text-sm w-full mt-4 flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          <span>{isExporting ? 'Exporting...' : 'Export Full Data'}</span>
        </button>
      </div>

      {/* Danger Zone Card */}
      <div className="card border-red-500/30 dark:border-red-500/50 mt-8">
        <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5" />
          <span>Danger Zone</span>
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 mb-4">
          These actions are permanent and cannot be undone. Proceed with caution.
        </p>
        <button
          onClick={handleClearAll}
          className="btn-secondary text-sm bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/40 w-full flex items-center justify-center space-x-2"
        >
          <Trash2 className="w-4 h-4" />
          <span>Delete All Tracked Products</span>
        </button>
      </div>
    </div>
  );
}