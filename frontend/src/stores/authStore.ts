import { create } from 'zustand';
import { api } from '../services/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (tenantName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  isAuthenticated: false,
  userEmail: null,
  login: async (email, password) => {
    const res: any = await api.post('/auth/login', { email, password });
    api.setToken(res.access_token);
    set({ token: res.access_token, isAuthenticated: true, userEmail: email });
  },
  register: async (tenantName, email, password) => {
    const res: any = await api.post('/auth/register', { tenant_name: tenantName, email, password });
    api.setToken(res.access_token);
    set({ token: res.access_token, isAuthenticated: true, userEmail: email });
  },
  logout: () => {
    api.clearToken();
    set({ token: null, isAuthenticated: false, userEmail: null });
  },
}));
