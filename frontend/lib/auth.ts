/**
 * Frontend Auth Utilities
 * JWT cookie management + auth API calls
 */

import Cookies from 'js-cookie';
import api from './api';

const TOKEN_KEY = 'flightai_token';
const TOKEN_EXPIRY_DAYS = 7;

// ==================== TOKEN MANAGEMENT ====================

export const setToken = (token: string): void => {
  Cookies.set(TOKEN_KEY, token, { expires: TOKEN_EXPIRY_DAYS, sameSite: 'lax' });
};

export const getToken = (): string | undefined => {
  return Cookies.get(TOKEN_KEY);
};

export const removeToken = (): void => {
  Cookies.remove(TOKEN_KEY);
};

export const isAuthenticated = (): boolean => {
  const token = getToken();
  if (!token) return false;

  // Check if token is expired by decoding payload
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
};

export const getCurrentUser = (): { user_id: string; email: string; name: string } | null => {
  const token = getToken();
  if (!token) return null;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp * 1000 < Date.now()) return null;
    return {
      user_id: payload.sub,
      email: payload.email,
      name: payload.name,
    };
  } catch {
    return null;
  }
};

export const authHeaders = (): Record<string, string> => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ==================== AUTH API CALLS ====================

export interface SignupData {
  email: string;
  password: string;
  name: string;
  home_airport?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResult {
  token: string;
  user_id: string;
  email: string;
  name: string;
}

export const signup = async (data: SignupData): Promise<AuthResult> => {
  const response = await api.post<AuthResult>('/auth/signup', data);
  setToken(response.data.token);
  return response.data;
};

export const login = async (data: LoginData): Promise<AuthResult> => {
  const response = await api.post<AuthResult>('/auth/login', data);
  setToken(response.data.token);
  return response.data;
};

export const logout = (): void => {
  removeToken();
};
