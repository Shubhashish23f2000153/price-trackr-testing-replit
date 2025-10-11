import { Sun, Bell, Shield, Download } from 'lucide-react';

interface SettingsProps {
  darkMode: boolean
  setDarkMode: (value: boolean) => void
}

export default function Settings({ darkMode, setDarkMode }: SettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Settings</h2>
        <p className="text-gray-600 dark:text-gray-400">Configure your price tracking preferences and notifications</p>
      </div>

      {/* Appearance */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
          <Sun className="w-5 h-5" />
          <span>Appearance</span>
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label htmlFor="theme-select" className="font-medium">Theme</label>
              <div className="text-sm text-gray-500">Choose your preferred theme</div>
            </div>
            <select
              id="theme-select"
              value={darkMode ? 'dark' : 'light'}
              onChange={(e) => setDarkMode(e.target.value === 'dark')}
              className="input w-32"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              {/* ADDED ID TO SPAN */}
              <span id="compact-mode-label" className="font-medium">Compact Mode</span>
              <div className="text-sm text-gray-500">Reduce spacing between elements</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              {/* LINKED SPAN TO INPUT WITH aria-labelledby */}
              <input type="checkbox" aria-labelledby="compact-mode-label" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black dark:peer-checked:bg-white"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
          <Bell className="w-5 h-5" />
          <span>Notifications</span>
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span id="push-label" className="font-medium">Push Notifications</span>
              <div className="text-sm text-gray-500">Receive browser notifications</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" aria-labelledby="push-label" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black dark:peer-checked:bg-white"></div>
            </label>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <span id="price-drop-label" className="font-medium">Price Drop Alerts</span>
              <div className="text-sm text-gray-500">Notify when prices fall below threshold</div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" aria-labelledby="price-drop-label" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-black dark:peer-checked:bg-white"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Regional Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Regional Settings</h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="country-select" className="block text-sm font-medium mb-2">Country</label>
            <select id="country-select" className="input">
              <option>India - India (₹)</option>
              <option>USA - USA ($)</option>
            </select>
          </div>
          <div>
            <label htmlFor="timezone-select" className="block text-sm font-medium mb-2">Time Zone</label>
            <select id="timezone-select" className="input">
              <option>IST - UTC + 5:30</option>
              <option>PST - UTC - 8:00</option>
            </select>
          </div>
        </div>
      </div>

      {/* Space Information */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Space Information</h3>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Tracked Items</span>
            <span className="font-medium">0 items</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Storage Used</span>
            <span className="font-medium">0 MB</span>
          </div>
        </div>
        <button className="btn-secondary text-sm w-full mt-4 flex items-center justify-center space-x-2">
          <Download className="w-4 h-4" />
          <span>Export Data</span>
        </button>
      </div>
    </div>
  )
}