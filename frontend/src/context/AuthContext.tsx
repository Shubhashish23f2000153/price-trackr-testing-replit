import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { setAuthToken, UserResponse, mergeAnonymousData } from '../services/api';

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
  anonymousId: string; // 3. Add anonymousId to context
  getAuthIdentifier: () => string | null; // 4. Add helper function
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
  const [anonymousId, setAnonymousId] = useState<string>(getAnonymousId()); // 5. Init anonymousId state
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUserFromToken = async () => {
      if (token) {
        setAuthToken(token);
        try {
          // Placeholder: Fetch user data from a '/api/users/me' endpoint
          const decoded = JSON.parse(atob(token.split('.')[1]));
          // NOTE: 'decoded.sub' is the user's email, which we'll use as the ID for now.
          setUser({ email: decoded.sub } as UserResponse); 
        } catch (error) {
          console.error("Failed to load user from token:", error);
          setToken(null);
          localStorage.removeItem('token');
          setAuthToken(null);
        }
      }
      setIsLoading(false);
    };
    loadUserFromToken();
  }, [token]);

  // 6. Create a function to get the correct ID (anon or user)
  const getAuthIdentifier = () => {
    if (user && token) {
      // We'll use the user's email as the unique string ID,
      // since that's what's in the token.
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

    // --- 7. THE MERGE ---
    // After login, merge the old anonymous data to the new user account.
    try {
      await mergeAnonymousData(anonymousId);
      console.log("Anonymous data merged successfully.");
      // Clear the old anonymous ID and get a new one for "guest" browsing
      localStorage.removeItem('anonymousId');
      setAnonymousId(getAnonymousId());
    } catch (error) {
      console.error("Failed to merge anonymous data:", error);
    }
    // --- End of Merge ---
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, anonymousId, getAuthIdentifier, login, logout, isLoading }}>
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