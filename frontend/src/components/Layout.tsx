import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, ListChecks, Plus, Tag, Settings, User, LogOut, LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { useEffect } from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { user, logout, getAuthIdentifier } = useAuth();
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'PRICE_ALERT') {
      const currentIdentifier = getAuthIdentifier();

      // --- ADD THIS CHECK ---
      // Get the setting from localStorage (default to true if not found)
      const alertsEnabled = localStorage.getItem('priceDropAlertsEnabled') !== 'false';

      // Only show alert if it's for this user AND alerts are enabled
      if (alertsEnabled && lastMessage.user_id === currentIdentifier) {
      // --- END CHECK ---

        // (We can improve this later with a nicer notification component)
        alert(
          `🔔 PRICE ALERT! 🔔\n\nA product on your watchlist has dropped in price!\n\nProduct ID: ${lastMessage.product_id}\nPrice: ₹${lastMessage.current_price}\nYour Alert: Below ₹${lastMessage.alert_price}`
        );
      }
    }
  }, [lastMessage, getAuthIdentifier]); // Added getAuthIdentifier dependency


  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/watchlist', icon: ListChecks, label: 'Watchlist' },
    { path: '/add', icon: Plus, label: 'Add' },
    { path: '/sales', icon: Tag, label: 'Sales' },
    { path: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-black dark:bg-white rounded-md flex items-center justify-center">
                <span className="text-white dark:text-black font-bold text-sm">PT</span>
              </div>
              <h1 className="text-xl font-semibold">PriceTrackr</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <span className="text-sm text-gray-600 dark:text-gray-400">hi, {user.email}</span>
                  <User className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <button onClick={logout} title="Logout" className="p-1 text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white">
                    <LogOut className="w-5 h-5" />
                  </button>
                </>
              ) : (
                <Link to="/login" className="flex items-center space-x-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white">
                  <LogIn className="w-5 h-5" />
                  <span>Login</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-3 text-sm font-medium border-b-2 transition-colors ${
                    isActive
                      ? 'border-black dark:border-white text-gray-900 dark:text-white'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 bg-gray-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>All prices displayed are approximate and sourced from publicly available information</p>
          <p className="mt-1">This application does not store credit cards or handle transactions</p>
        </div>
      </footer>
    </div>
  );
}