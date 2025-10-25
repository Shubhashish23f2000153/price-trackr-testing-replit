import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { setAuthToken, UserResponse } from '../services/api'; // Import UserResponse

// Define the shape of the context
interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define the provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUserFromToken = async () => {
      if (token) {
        setAuthToken(token); // Set token for all future API calls
        try {
          // TODO: Add a '/api/users/me' endpoint to your backend
          // to fetch user data from the token.
          
          // Placeholder: We'll just assume the token is valid for now
          // and decode it to get email (this is insecure, but works for UI)
          const decoded = JSON.parse(atob(token.split('.')[1]));
          setUser({ email: decoded.sub } as UserResponse);
        } catch (error) {
          console.error("Failed to load user from token:", error);
          // Token is invalid
          setToken(null);
          localStorage.removeItem('token');
          setAuthToken(null);
        }
      }
      setIsLoading(false);
    };
    loadUserFromToken();
  }, [token]);

  const login = async (email: string, password: string) => {
    const response = await api.post('/users/login', { email, password });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setAuthToken(access_token);
    // Set user from the token's payload
    const decoded = JSON.parse(atob(access_token.split('.')[1]));
    setUser({ email: decoded.sub } as UserResponse);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};