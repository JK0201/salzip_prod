import client from './client';

type SessionResponse = {
  token: string;
  expires_at: string; // ISO 8601
};

type AuthResponse = {
  token: string;
  expires_at: string;
  user: { id: string; email: string; name: string };
};

export async function createSession(): Promise<SessionResponse> {
  const res = await client.post<SessionResponse>('/api/v1/session');
  return res.data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await client.post<AuthResponse>('/api/v1/auth/login', { email, password });
  return res.data;
}

export async function signup(name: string, email: string, password: string): Promise<AuthResponse> {
  const res = await client.post<AuthResponse>('/api/v1/auth/signup', { name, email, password });
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post('/api/v1/auth/logout');
}
