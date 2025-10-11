import { useState, useEffect } from 'react';
import { Sun, Bell, Shield, Download } from 'lucide-react';
import { getSpaceStats } from '../services/api';
import { countries, timezones } from '../utils/regionalData'; // Import the new data

interface SettingsProps {
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}

export default function Settings({ darkMode, setDarkMode }: SettingsProps) {
  const [spaceInfo, setSpaceInfo] = useState({ tracked_items: 0, price_points: 0 });
  const [selectedCountry, setSelectedCountry] = useState(countries[0].value);
  const [selectedTimezone, setSelectedTimezone] = useState(timezones[0].value);

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
            <select id="country-select" className="input" value={selectedCountry} onChange={(e) => setSelectedCountry(e.target.value)}>
              {countries.map(country => (
                <option key={country.value} value={country.value}>{country.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="timezone-select" className="block text-sm font-medium mb-2">Time Zone</label>
            <select id="timezone-select" className="input" value={selectedTimezone} onChange={(e) => setSelectedTimezone(e.target.value)}>
              {timezones.map(tz => (
                <option key={tz.value} value={tz.value}>{tz.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Other cards ... */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Bell className="w-5 h-5" /><span>Notifications</span></h3>
        {/* Notification settings go here */}
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2"><Shield className="w-5 h-5" /><span>Privacy & Security</span></h3>
        {/* Privacy settings go here */}
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
            <span className="text-gray-600 dark:text-gray-400">Price Points</span>
            <span className="font-medium">{spaceInfo.price_points} records</span>
          </div>
        </div>
        <button className="btn-secondary text-sm w-full mt-4 flex items-center justify-center space-x-2">
          <Download className="w-4 h-4" />
          <span>Export Data</span>
        </button>
      </div>
    </div>
  );
}