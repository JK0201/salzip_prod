import { create } from 'zustand';

export const SESSION_KEY = 'session_token';
export const SESSION_EXPIRES_KEY = 'session_expires_at';
export const USER_NAME_KEY = 'user_name';

interface SessionState {
  token: string | null;
  expiresAt: string | null; // ISO 8601
  userName: string | null;
  setSession: (token: string, expiresAt: string) => void;
  setUserName: (name: string | null) => void;
  clearSession: () => void;
  isExpired: () => boolean;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  token: null,
  expiresAt: null,
  userName: null,

  setSession: (token, expiresAt) => set({ token, expiresAt }),

  setUserName: (name) => set({ userName: name }),

  clearSession: () => set({ token: null, expiresAt: null, userName: null }),

  isExpired: () => {
    const { expiresAt } = get();
    if (!expiresAt) return true;
    return new Date(expiresAt) <= new Date();
  },
}));
