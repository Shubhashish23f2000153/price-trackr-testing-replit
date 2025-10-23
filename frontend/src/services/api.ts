import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
}

export interface ProductDetail extends Product {
  prices: PriceInfo[];
  lowest_ever_price?: number;
  is_in_watchlist: boolean;
}

// Ensure PriceHistoryItem is exported
export interface PriceHistoryItem {
    date: string; // Keep as string for chart compatibility
    price: number;
    source: string;
}

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

// Add the Sale type definition if it's missing
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
  // Use the /track endpoint, NOT /add-from-extension for the web app form
  const response = await api.post('/products/track', { url, title: 'Loading...' }); 
  return response.data;
};

// Removed duplicate trackProduct
// export const trackProduct = async (url: string) => { ... }

export const deleteProduct = async (productId: number) => {
  const response = await api.delete(`/products/${productId}`);
  return response.data;
};

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

// Add this function definition
export const updateWatchlistAlert = async (watchlistId: number, alertPrice: number) => {
  const alertRules = { threshold: alertPrice, type: 'below' }; // Define the rule structure
  const response = await api.put(`/watchlist/${watchlistId}`, { alert_rules: alertRules });
  return response.data;
};

// Placeholder: Needs implementation - Requires finding the watchlist item ID first
export const removeFromWatchlist = async (watchlistId: number) => {
    console.warn("removeFromWatchlist needs implementation with the correct watchlist ID");
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
  if (region) {
    params.region = region;
  }
  if (status) {
    params.status = status;
  }
  
  const response = await api.get<Sale[]>('/sales/', { params });
  return response.data;
};

export const deleteAllProducts = async () => {
  const response = await api.delete('/products/all');
  return response.data;
};

export default api;