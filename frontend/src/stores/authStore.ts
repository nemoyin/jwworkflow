import { create } from 'zustand';
import { api, TOKEN_KEY, TOKEN_EMAIL_KEY } from '../services/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  userEmail: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (tenantName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

// 模块加载时从 localStorage 恢复登录态（刷新/重启浏览器后保持登录）
const persistedToken = localStorage.getItem(TOKEN_KEY);
const persistedEmail = localStorage.getItem(TOKEN_EMAIL_KEY);

export const useAuthStore = create<AuthState>((set) => ({
  token: persistedToken,
  isAuthenticated: !!persistedToken,
  userEmail: persistedEmail,
  login: async (email, password) => {
    const res: any = await api.post('/auth/login', { email, password });
    api.setToken(res.access_token); // setToken 内部已写入 localStorage
    localStorage.setItem(TOKEN_EMAIL_KEY, email);
    set({ token: res.access_token, isAuthenticated: true, userEmail: email });
  },
  register: async (tenantName, email, password) => {
    const res: any = await api.post('/auth/register', { tenant_name: tenantName, email, password });
    api.setToken(res.access_token); // setToken 内部已写入 localStorage
    localStorage.setItem(TOKEN_EMAIL_KEY, email);
    set({ token: res.access_token, isAuthenticated: true, userEmail: email });
  },
  logout: () => {
    api.clearToken();
    localStorage.removeItem(TOKEN_EMAIL_KEY);
    set({ token: null, isAuthenticated: false, userEmail: null });
  },
}));
