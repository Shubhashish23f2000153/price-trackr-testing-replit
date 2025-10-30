import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
// --- 1. RENAMED THE IMPORT to fix name collision ---
import api, { setAuthToken, setAnonymousId as apiSetAnonymousId, UserResponse, mergeAnonymousData } from '../services/api';

// --- 2. Helper function for anonymous ID ---
const getAnonymousId = (): string => {
  let anonId = localStorage.getItem('anonymousId');
  if (!anonId) {
    anonId = crypto.randomUUID();
    localStorage.setItem('anonymousId', anonId);
  }
  return anonId;
};

// Define the shape of the context
interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  anonymousId: string; // Add anonymousId to context
  getAuthIdentifier: () => string | null; // Add helper function
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
  // --- This 'setAnonymousId' is the state setter, which is fine (though unused, which is just a warning) ---
  const [anonymousId, setAnonymousId] = useState<string>(getAnonymousId()); 
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUserFromToken = async () => {
      if (token) {
        setAuthToken(token);
        apiSetAnonymousId(null); // <-- 2. Use the renamed import
        try {
          const decoded = JSON.parse(atob(token.split('.')[1]));
          
          // ADD EXPIRATION CHECK
          if (decoded.exp * 1000 < Date.now()) {
            console.warn("Token expired, logging out.");
            throw new Error("Token expired"); // Jump to catch block
          }

          setUser({ email: decoded.sub } as UserResponse); 
        } catch (error) {
          console.error("Failed to load user from token (purging):", error);
          // FULLY LOG OUT on error/expiration
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
          setAuthToken(null);
          apiSetAnonymousId(anonymousId); // <-- 3. Use the renamed import
        }
      } else {
        // THIS IS THE KEY FIX
        // No token, so user is anonymous. Set the anonymous header.
        setAuthToken(null);
        apiSetAnonymousId(anonymousId); // <-- 4. Use the renamed import
      }
      setIsLoading(false);
    };
    loadUserFromToken();
  }, [token, anonymousId]); // Add anonymousId to dependency array

  // Create a function to get the correct ID (anon or user)
  const getAuthIdentifier = () => {
    if (user && token) {
      return user.email;
    }
    return anonymousId;
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/users/login', { email, password });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setAuthToken(access_token);
    
    const decoded = JSON.parse(atob(access_token.split('.')[1]));
    const loggedInUser = { email: decoded.sub } as UserResponse;
    setUser(loggedInUser);

    // --- THE MERGE ---
    try {
      await mergeAnonymousData(anonymousId);
      console.log("Anonymous data merged successfully.");
      // Clear the old anonymous ID and get a new one for "guest" browsing
      localStorage.removeItem('anonymousId');
      setAnonymousId(getAnonymousId()); // This will call the state setter
    } catch (error) {
      console.error("Failed to merge anonymous data:", error);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
    // On logout, ensure we set the anonymous header for guest browsing
    apiSetAnonymousId(anonymousId); 
  };

  return (
    <AuthContext.Provider value={{ user, token, anonymousId, getAuthIdentifier, login, logout, isLoading }}>
      {!isLoading && children}
    {/* --- 3. FIXED THE TYPO HERE --- */}
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