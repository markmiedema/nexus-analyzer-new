'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  tenant_id: string;
  role: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginData) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const refreshAuth = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
        credentials: 'include', // Send httpOnly cookies
      });

      if (response.ok) {
        const userData = await response.json();
        // Add full_name for convenience
        userData.full_name = `${userData.first_name} ${userData.last_name}`;
        setUser(userData);
      } else {
        // Not authenticated
        setUser(null);
      }
    } catch (error) {
      console.error('Auth refresh error:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl]);

  // Check authentication status on mount
  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const login = async (credentials: LoginData) => {
    try {
      const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Send and receive httpOnly cookies
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password,
          tenant_subdomain: 'demo', // Default tenant for demo
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      // Login successful, cookies are set automatically
      const userData = await response.json();

      // Add full_name for convenience
      userData.full_name = `${userData.first_name} ${userData.last_name}`;
      setUser(userData);

      router.push('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call backend logout to clear cookies
      await fetch(`${apiUrl}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      router.push('/login');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
