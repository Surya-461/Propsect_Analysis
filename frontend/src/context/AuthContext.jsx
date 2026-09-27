import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('prospect_ai_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('prospect_ai_token') || null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState('');

  const logout = useCallback(async () => {
    try {
      const currentToken = localStorage.getItem('prospect_ai_token');
      if (currentToken) {
        await client.post('/auth/logout').catch(() => {});
      }
    } finally {
      localStorage.removeItem('prospect_ai_token');
      localStorage.removeItem('prospect_ai_user');
      setToken(null);
      setUser(null);
      setAuthError('');
    }
  }, []);

  // Validate session on mount
  useEffect(() => {
    let isMounted = true;
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('prospect_ai_token');
      if (storedToken) {
        try {
          const res = await Promise.race([
            client.get('/auth/me'),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 4000))
          ]);
          if (isMounted && res && res.data) {
            setUser(res.data);
            localStorage.setItem('prospect_ai_user', JSON.stringify(res.data));
          }
        } catch {
          // Token invalid, expired, or backend unreachable
          if (isMounted) {
            localStorage.removeItem('prospect_ai_token');
            localStorage.removeItem('prospect_ai_user');
            setToken(null);
            setUser(null);
          }
        }
      }
      if (isMounted) {
        setLoading(false);
      }
    };

    verifyToken();

    // Listen for global 401 unauthorized events
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [logout]);


  const login = async (email, password) => {
    setAuthError('');
    try {
      const res = await client.post('/auth/login', { email, password });
      const { access_token, user: loggedUser } = res.data;

      localStorage.setItem('prospect_ai_token', access_token);
      localStorage.setItem('prospect_ai_user', JSON.stringify(loggedUser));

      setToken(access_token);
      setUser(loggedUser);
      return { success: true };
    } catch (err) {
      let message = 'Invalid email or password. Please try again.';
      if (!err.response) {
        message = 'Cannot connect to backend server. Please ensure FastAPI backend is running on http://localhost:8000.';
      } else if (typeof err.response.data?.detail === 'string') {
        message = err.response.data.detail;
      } else if (err.response.data?.message) {
        message = err.response.data.message;
      }
      setAuthError(message);
      return { success: false, message };
    }
  };

  const signup = async (name, email, password) => {
    setAuthError('');
    try {
      const res = await client.post('/auth/signup', { name, email, password });
      const { access_token, user: newUser } = res.data;

      localStorage.setItem('prospect_ai_token', access_token);
      localStorage.setItem('prospect_ai_user', JSON.stringify(newUser));

      setToken(access_token);
      setUser(newUser);
      return { success: true };
    } catch (err) {
      let message = 'Registration failed. Please check your details.';
      if (!err.response) {
        message = 'Cannot connect to backend server. Please ensure FastAPI backend is running on http://localhost:8000.';
      } else if (typeof err.response.data?.detail === 'string') {
        message = err.response.data.detail;
      } else if (err.response.data?.message) {
        message = err.response.data.message;
      }
      setAuthError(message);
      return { success: false, message };
    }
  };

  const loginWithGoogle = async (googleData) => {
    setAuthError('');
    try {
      const res = await client.post('/auth/google', googleData);
      const { access_token, user: loggedUser } = res.data;

      localStorage.setItem('prospect_ai_token', access_token);
      localStorage.setItem('prospect_ai_user', JSON.stringify(loggedUser));

      setToken(access_token);
      setUser(loggedUser);
      return { success: true, user: loggedUser };
    } catch (err) {
      let message = 'Google authentication failed. Please try again.';
      if (!err.response) {
        message = 'Cannot connect to backend server. Please ensure FastAPI backend is running on http://localhost:8000.';
      } else if (typeof err.response.data?.detail === 'string') {
        message = err.response.data.detail;
      } else if (err.response.data?.message) {
        message = err.response.data.message;
      }
      setAuthError(message);
      return { success: false, message };
    }
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    loading,
    authError,
    setAuthError,
    login,
    signup,
    loginWithGoogle,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
