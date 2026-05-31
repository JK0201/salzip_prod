import {
  SESSION_EXPIRES_KEY,
  SESSION_KEY,
  useSessionStore,
} from '@/store/useSessionStore';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosRequestConfig } from 'axios';
import { API_BASE_URL as BASE_URL } from '@/constants/env';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = useSessionStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const config = error.config as AxiosRequestConfig & { _retry?: boolean };

    const body = error.response?.data as
      | { error?: string; detail?: string }
      | undefined;
    const isLoginRequired =
      body?.error === 'login required' || body?.detail === 'login required';

    // 익명 유저(userName 없음)만 401 시 익명 세션 재발급 허용.
    // 로그인 유저(userName 있음)는 익명으로 덮지 않음 → reject → 로그인 화면 분기.
    const { userName } = useSessionStore.getState();
    const canReissueAnon =
      error.response?.status === 401 &&
      !config._retry &&
      !isLoginRequired &&
      !userName;

    if (canReissueAnon) {
      config._retry = true;

      // 순환 참조 방지를 위해 axios 직접 호출
      const { data } = await axios.post<{ token: string; expires_at: string }>(
        `${BASE_URL}/api/v1/session`,
      );
      await AsyncStorage.setItem(SESSION_KEY, data.token);
      await AsyncStorage.setItem(SESSION_EXPIRES_KEY, data.expires_at);
      useSessionStore.getState().setSession(data.token, data.expires_at);

      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${data.token}`,
      };
      return client(config);
    }

    return Promise.reject(error);
  },
);

export default client;
