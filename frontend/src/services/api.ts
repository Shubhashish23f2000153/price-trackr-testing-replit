import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// --- THIS IS THE CRITICAL CHANGE ---
// We replace the failing import.meta.env with a simple placeholder.
const VAPID_PUBLIC_KEY = 'VITE_VAPID_PUBLIC_KEY_PLACEHOLDER';
// --- END CHANGE ---

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Function to set auth token ---
export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

// --- Function to set anonymous ID header ---
export const setAnonymousId = (anonId: string | null) => {
  if (anonId) {
    api.defaults.headers.common['X-Anonymous-ID'] = anonId;
  } else {
    delete api.defaults.headers.common['X-Anonymous-ID'];
  }
};


// --- TYPE DEFINITIONS ---
export interface Product {
  id: number;
  title: string;
  sku?: string;
  brand?: string;
  category?: string;
  image_url?: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface PriceInfo {
  source_name: string;
  current_price: number;
  currency: string;
  availability: string;
  in_stock: boolean;
  url: string;
  seller_name?: string | null;
  seller_rating?: string | null;
  seller_review_count?: string | null;
  avg_review_sentiment?: number | null; // Added Optional number field
}

export interface ProductDetail extends Product {
  prices: PriceInfo[];
  lowest_ever_price?: number;
  is_in_watchlist: boolean;
}

export interface PriceHistoryItem {
    date: string;
    price: number;
    source: string;
}

// --- NEW INTERFACE FOR EXPORT ---
export interface ProductWithHistory extends Product {
  price_history: PriceHistoryItem[];
}
// --- END NEW INTERFACE ---

export interface Watchlist {
  id: number;
  user_id?: string;
  product_id: number;
  alert_rules?: any;
  created_at: string;
}

export interface SpaceStats {
  tracked_items: number;
  price_points: number;
}

export interface DashboardStats {
  total_products: number;
  active_deals: number;
  price_drops: number;
  total_saved: number;
}

export interface Sale {
  id: number;
  title: string;
  description?: string;
  discount_percentage?: number;
  source_domain: string;
  region: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  created_at: string;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface ScamScore {
  domain: string;
  score: number;
  trust_level: 'high' | 'medium' | 'low' | 'unknown';
  whois_days_old?: number;
  safe_browsing_flag: boolean;
  message?: string;
}


// --- API FUNCTIONS ---

// Products API
export const getProducts = async (skip = 0, limit = 100): Promise<Product[]> => {
  const response = await api.get('/products/', { params: { skip, limit } });
  return response.data;
};

export const getProduct = async (productId: number): Promise<ProductDetail> => {
  const response = await api.get(`/products/${productId}`);
  return response.data;
};

export const getPriceHistory = async (productId: number, days = 30): Promise<PriceHistoryItem[]> => {
  const response = await api.get(`/products/${productId}/history`, { params: { days } });
  return response.data;
};

export const trackProduct = async (url: string) => {
  const response = await api.post('/products/track', { url, title: 'Loading...' });
  return response.data;
};

export const deleteProduct = async (productId: number) => {
  const response = await api.delete(`/products/${productId}`);
  return response.data;
};

// --- NEW EXPORT FUNCTION ---
export const exportAllData = async (): Promise<ProductWithHistory[]> => {
  const response = await api.get('/products/export');
  return response.data;
};
// --- END NEW FUNCTION ---

// Watchlist API
export const getWatchlist = async (): Promise<Watchlist[]> => {
    const response = await api.get('/watchlist/');
    return response.data;
};

export const addToWatchlist = async (productId: number, alertRules?: any) => {
    const response = await api.post('/watchlist/', {
        product_id: productId,
        alert_rules: alertRules,
    });
    return response.data;
};

export const updateWatchlistAlert = async (watchlistId: number, alertPrice: number) => {
  const alertRules = { threshold: alertPrice, type: 'below' };
  const response = await api.put(`/watchlist/${watchlistId}`, { alert_rules: alertRules });
  return response.data;
};

export const removeFromWatchlist = async (watchlistId: number) => {
    const response = await api.delete(`/watchlist/${watchlistId}`);
    return response.data;
};

// Stats API
export const getSpaceStats = async (): Promise<SpaceStats> => {
  const response = await api.get('/stats/space');
  return response.data;
};

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get('/stats/dashboard');
  return response.data;
};

// Sales API
export const getSales = async (region?: string, status?: 'ongoing' | 'upcoming'): Promise<Sale[]> => {
  const params: { region?: string; status?: string } = {};
  if (region) params.region = region;
  if (status) params.status = status;

  const response = await api.get<Sale[]>('/sales/', { params });
  return response.data;
};

export const deleteAllProducts = async () => {
  const response = await api.delete('/products/all');
  return response.data;
};

// Auth API Functions
export const registerUser = async (email: string, password: string, fullName: string) => {
  const response = await api.post('/users/register', { email, password, full_name: fullName });
  return response.data;
};

export const mergeAnonymousData = async (anonId: string) => {
  const response = await api.post('/users/merge', {}, {
    headers: {
      'X-Anonymous-ID': anonId
    }
  });
  return response.data;
}

// Scam API Function
export const getScamScore = async (domain: string): Promise<ScamScore> => {
  const response = await api.get('/scam/check', { params: { domain } });
  return response.data;
};

// --- DELETE USER FUNCTION ---
export const deleteUser = async () => {
  // Uses the DELETE /users/me endpoint we created
  // Requires the user to be logged in (Authorization header is set by setAuthToken)
  const response = await api.delete('/users/me');
  return response.data; // Should return {"message": "User account deleted successfully"}
};
// --- END DELETE USER FUNCTION ---

export const updatePushSubscription = async (
  subscription: PushSubscriptionJSON | null
): Promise<UserResponse> => {
  // Uses the POST /users/subscribe endpoint we created
  const response = await api.post('/users/subscribe', { subscription });
  return response.data;
};
// --- END NEW FUNCTION ---

// --- EXPORT THE VAPID KEY ---
export { VAPID_PUBLIC_KEY };
// --- END EXPORT ---

export default api;