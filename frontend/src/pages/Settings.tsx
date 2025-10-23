import { useState, useEffect } from 'react';
import { Sun, Bell, Shield, Download, Trash2, AlertTriangle } from 'lucide-react';
import { getSpaceStats, deleteAllProducts } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface SettingsProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

export default function Settings({ darkMode, setDarkMode }: SettingsProps) {
  const [spaceInfo, setSpaceInfo] = useState({ tracked_items: 0, price_points: 0 });
  const navigate = useNavigate();

  // Fetch space stats when the component mounts
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
  }, []); // Empty dependency array ensures this runs only once on mount

  // Handler for the "Clear All" button
  const handleClearAll = async () => {
    if (window.confirm("DANGER ZONE:\nAre you absolutely sure you want to delete ALL tracked products?\nThis action cannot be undone.")) {
      try {
        const result = await deleteAllProducts();
        alert(result.message); // Show success message
        // Refetch stats to show 0
        const updatedStats = await getSpaceStats();
        setSpaceInfo(updatedStats);
        navigate('/'); // Go to dashboard after clearing
      } catch (error) {
        console.error("Failed to delete all products:", error);
        alert("Failed to delete all products. Please try again.");
      }
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

      {/* Regional Settings Card */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Regional Settings</h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="country-select" className="block text-sm font-medium mb-2">Country</label>
            <select id="country-select" className="input">
              <option>India - India (₹)</option>
              <option>USA - USA ($)</option>
              <option>UK - GBP (£)</option>
            </select>
          </div>
          <div>
            <label htmlFor="timezone-select" className="block text-sm font-medium mb-2">Time Zone</label>
            <select id="timezone-select" className="input">
              <option>IST - UTC + 5:30</option>
              <option>PST - UTC - 8:00</option>
              <option>GMT - UTC + 0:00</option>
            </select>
          </div>
        </div>
      </div>

       {/* Notifications Card - Placeholder */}
       <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Bell className="w-5 h-5" /><span>Notifications</span></h3>
        <p className="text-sm text-gray-500">Notification settings will go here.</p>
      </div>

       {/* Privacy & Security Card - Placeholder */}
       <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Shield className="w-5 h-5" /><span>Privacy & Security</span></h3>
         <p className="text-sm text-gray-500">Privacy settings will go here.</p>
      </div>

      {/* Space Information Card - Now Dynamic */}
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
          {/* Storage Used calculation would require more backend logic */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Storage Used</span>
            <span className="font-medium">N/A</span>
          </div>
        </div>
        <button className="btn-secondary text-sm w-full mt-4 flex items-center justify-center space-x-2">
          <Download className="w-4 h-4" />
          <span>Export Data</span>
        </button>
      </div>

      {/* Danger Zone: Clear All Button */}
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