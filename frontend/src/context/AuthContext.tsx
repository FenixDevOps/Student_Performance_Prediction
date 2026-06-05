import React, { createContext, useState, useEffect } from 'react';
import { User, AuthState } from '../types';
import { authService } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (payload: any) => Promise<void>;
  logout: () => void;
  updateUser: (updatedUser: User) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    loading: true,
  });

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setState({ user: null, token: null, loading: false });
        return;
      }

      try {
        const user = await authService.getMe();
        setState({ user, token, loading: false });
      } catch (err) {
        console.error('Failed to restore authentication session:', err);
        localStorage.removeItem('token');
        setState({ user: null, token: null, loading: false });
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    setState((prev) => ({ ...prev, loading: true }));
    try {
      const data = await authService.login(email, pass);
      const token = data.access_token;
      localStorage.setItem('token', token);
      
      const user = await authService.getMe();
      localStorage.setItem('user', JSON.stringify(user));
      
      setState({ user, token, loading: false });
    } catch (err) {
      setState((prev) => ({ ...prev, loading: false }));
      throw err;
    }
  };

  const register = async (payload: any) => {
    setState((prev) => ({ ...prev, loading: true }));
    try {
      await authService.register(payload);
      // Auto login after signup
      await login(payload.email, payload.password);
    } catch (err) {
      setState((prev) => ({ ...prev, loading: false }));
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setState({ user: null, token: null, loading: false });
    window.location.href = '/login';
  };

  const updateUser = (updatedUser: User) => {
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setState((prev) => ({ ...prev, user: updatedUser }));
  };

  return (
    <AuthContext.Provider value={{
      user: state.user,
      token: state.token,
      loading: state.loading,
      login,
      register,
      logout,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};
