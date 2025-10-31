import { useState, useEffect } from 'react';
import { Sun, Bell, Shield, Download, Trash2, AlertTriangle, MapPin, UserX } from 'lucide-react';
import { 
  getSpaceStats, 
  deleteAllProducts, 
  deleteUser,  
  exportAllData, 
  ProductWithHistory,
  updatePushSubscription,
  VAPID_PUBLIC_KEY
} from '../services/api';
import { useNavigate } from 'react-router-dom';
import { countries } from '../utils/regionalData';
import { useAuth } from '../context/AuthContext';


// --- SettingsProps Interface ---
interface SettingsProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}


// --- ToggleSwitchProps Interface (with disabled prop) ---
interface ToggleSwitchProps {
  label: string;
  description: string;
  enabled: boolean;
  setEnabled: (value: boolean) => void;
  disabled?: boolean;
}


// --- ToggleSwitch Component (with disabled logic) ---
function ToggleSwitch({ label, description, enabled, setEnabled, disabled = false }: ToggleSwitchProps) {
  return (
    <div className={`flex items-center justify-between ${disabled ? 'opacity-50' : ''}`}>
      <div>
        <label className="font-medium">{label}</label>
        <div className="text-sm text-gray-500">{description}</div>
      </div>
      <button
        onClick={() => setEnabled(!enabled)}
        disabled={disabled}
        className={`flex items-center p-1 rounded-full w-12 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black dark:focus:ring-offset-gray-900 dark:focus:ring-white ${
          enabled ? 'bg-black dark:bg-white justify-end' : 'bg-gray-200 dark:bg-gray-700 justify-start'
        } ${disabled ? 'cursor-not-allowed' : ''}`}
        aria-label={`Toggle ${label}`}
      >
        <span className={`block w-5 h-5 rounded-full shadow-lg transform ring-0 transition duration-200 ease-in-out ${
          enabled ? 'bg-white dark:bg-black' : 'bg-white dark:bg-gray-300'
        }`}/>
      </button>
    </div>
  );
}


// --- ROBUST BASE64 DECODING HELPER ---
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  if (!base64String || typeof base64String !== 'string') {
    throw new Error('Invalid base64String provided');
  }

  const trimmed = base64String.trim();
  if (trimmed.length === 0) {
    throw new Error('Base64 string is empty');
  }

  const padding = '='.repeat((4 - (trimmed.length % 4)) % 4);
  const base64 = (trimmed + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  try {
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  } catch (error) {
    console.error('Error decoding Base64:', error);
    throw new Error(`Failed to decode Base64 string: ${(error as Error).message}`);
  }
}
// --- END HELPER ---



// --- Settings Component ---
export default function Settings({ darkMode, setDarkMode }: SettingsProps) {
  const [spaceInfo, setSpaceInfo] = useState({ tracked_items: 0, price_points: 0 });
  const navigate = useNavigate();
  const [country, setCountry] = useState(() => localStorage.getItem('userCountry') || 'IN');
  const [pushNotificationsEnabled, setPushNotificationsEnabled] = useState(() => localStorage.getItem('pushNotificationsEnabled') === 'true' ? true : false);
  const [priceDropAlertsEnabled, setPriceDropAlertsEnabled] = useState(() => localStorage.getItem('priceDropAlertsEnabled') === 'false' ? false : true);
  const [isExporting, setIsExporting] = useState(false);
  const { user, logout } = useAuth();
  const [isSubscribing, setIsSubscribing] = useState(false);


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


  // --- Subscription Logic ---
  const handlePushToggle = async (enabled: boolean) => {
    if (!user) {
      alert("You must be logged in to enable push notifications.");
      setPushNotificationsEnabled(false);
      localStorage.setItem('pushNotificationsEnabled', 'false');
      return;
    }


    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      alert("Push notifications are not supported by your browser.");
      return;
    }
    
    setIsSubscribing(true);

    // --- SAFETY CHECK (This fixes Error 1 by removing the '.length' check) ---
    if (!VAPID_PUBLIC_KEY || VAPID_PUBLIC_KEY === 'VITE_VAPID_PUBLIC_KEY_PLACEHOLDER') {
      console.error("VAPID key is missing or is still the placeholder. Build failed.");
      alert("Error: Push notification setup is incomplete on the server. Please contact support.");
      setIsSubscribing(false); 
      setPushNotificationsEnabled(false); 
      localStorage.setItem('pushNotificationsEnabled', 'false');
      return;
    }
    // --- END SAFETY CHECK ---


    try {
      if (enabled) {
        // --- SUBSCRIBE ---
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          throw new Error('Permission not granted for notifications');
        }

        let applicationServerKey: Uint8Array;
        try {
          applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);
        } catch (keyError) {
          console.error('Failed to process VAPID key:', keyError);
          throw new Error(`Invalid VAPID key format: ${(keyError as Error).message}`);
        }

        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          // --- THIS IS THE FIX for Error 2 ---
         applicationServerKey: applicationServerKey as BufferSource,
        });
        
        console.log("Push subscription successful:", subscription);
        await updatePushSubscription(subscription.toJSON());
        alert("Push notifications enabled!");
        setPushNotificationsEnabled(true);
        localStorage.setItem('pushNotificationsEnabled', 'true');


      } else {
        // --- UNSUBSCRIBE ---
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        
        if (subscription) {
          await subscription.unsubscribe();
          console.log("Push subscription cancelled.");
          await updatePushSubscription(null); 
          alert("Push notifications disabled.");
        }
        setPushNotificationsEnabled(false);
        localStorage.setItem('pushNotificationsEnabled', 'false');
      }


    } catch (error) {
      console.error('Failed to update push subscription:', error);
      const errorMessage = (error as Error).message || String(error);
      alert(`Error: ${errorMessage}. Notifications may not be enabled.`);
      setPushNotificationsEnabled(false);
      localStorage.setItem('pushNotificationsEnabled', 'false');
    } finally {
      setIsSubscribing(false);
    }
  };
  // --- END Subscription Logic ---


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
    alert("Starting data export. This may take a moment...");
    try {
      const productsWithHistory: ProductWithHistory[] = await exportAllData();


      if (!productsWithHistory || productsWithHistory.length === 0) {
        alert("No products found to export.");
        setIsExporting(false);
        return;
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
            setEnabled={handlePushToggle}
            disabled={isSubscribing}
          />
          <ToggleSwitch
            label="Price Drop Alerts"
            description="Notify when price drops below threshold"
            enabled={priceDropAlertsEnabled}
            setEnabled={setPriceDropAlertsEnabled}
            disabled={isSubscribing} 
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