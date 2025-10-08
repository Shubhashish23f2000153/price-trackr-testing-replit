import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  lowest_price?: number;
  highest_price?: number;
}

export interface ProductDetail extends Product {
  prices: PriceInfo[];
  lowest_ever_price?: number;
  is_in_watchlist: boolean;
}

export interface Watchlist {
  id: number;
  user_id?: string;
  product_id: number;
  alert_rules?: any;
  created_at: string;
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

// Products API
export const trackProduct = async (url: string) => {
  const response = await api.post('/products/track', {
    url,
    title: 'Loading...',
  });
  return response.data;
};

export const getProducts = async (skip = 0, limit = 100) => {
  const response = await api.get<Product[]>('/products/', {
    params: { skip, limit },
  });
  return response.data;
};

export const getProduct = async (productId: number) => {
  const response = await api.get<ProductDetail>(`/products/${productId}`);
  return response.data;
};

export const getPriceHistory = async (productId: number, days = 30) => {
  const response = await api.get(`/products/${productId}/history`, {
    params: { days },
  });
  return response.data;
};

export const deleteProduct = async (productId: number) => {
  const response = await api.delete(`/products/${productId}`);
  return response.data;
};

// Watchlist API
export const getWatchlist = async (userId?: string) => {
  const response = await api.get<Watchlist[]>('/watchlist/', {
    params: userId ? { user_id: userId } : {},
  });
  return response.data;
};

export const addToWatchlist = async (productId: number, alertRules?: any) => {
  const response = await api.post('/watchlist/', {
    product_id: productId,
    alert_rules: alertRules,
  });
  return response.data;
};

export const removeFromWatchlist = async (watchlistId: number) => {
  const response = await api.delete(`/watchlist/${watchlistId}`);
  return response.data;
};

// Sales API
export const getSales = async (region?: string) => {
  const response = await api.get<Sale[]>('/sales/', {
    params: region ? { region } : {},
  });
  return response.data;
};

export const createSale = async (saleData: Partial<Sale>) => {
  const response = await api.post('/sales/', saleData);
  return response.data;
};

// Scam Check API
export const checkScam = async (domain: string) => {
  const response = await api.get('/scam/check', {
    params: { domain },
  });
  return response.data;
};

export default api;
