// Route: _layout (루트 - 테마 프로바이더 + Stack)
import '../../global.css';
import { useEffect, useState } from 'react';
import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { Stack } from 'expo-router';
import { useColorScheme, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createSession } from '@/api/session';
import { useSessionStore, SESSION_KEY, SESSION_EXPIRES_KEY, USER_NAME_KEY } from '@/store/useSessionStore';
import { useFavoriteStore } from '@/store/useFavoriteStore';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const { setSession, setUserName } = useSessionStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    async function initSession() {
      const token = await AsyncStorage.getItem(SESSION_KEY);
      const expiresAt = await AsyncStorage.getItem(SESSION_EXPIRES_KEY);
      const name = await AsyncStorage.getItem(USER_NAME_KEY);
      if (name) setUserName(name);

      if (token && expiresAt && new Date(expiresAt) > new Date()) {
        setSession(token, expiresAt);
        console.log('[Session] 기존 토큰 사용:', token, '만료:', expiresAt);
        if (name) useFavoriteStore.getState().load(); // 로그인 유저 찜 목록 복원
        return;
      }

      // 로그인 유저(name 있음)는 만료 시 익명 발급 금지 → 로그인 화면이 처리.
      if (name) {
        console.log('[Session] 로그인 토큰 만료 → 재로그인 필요');
        return;
      }

      const session = await createSession();
      await AsyncStorage.setItem(SESSION_KEY, session.token);
      await AsyncStorage.setItem(SESSION_EXPIRES_KEY, session.expires_at);
      setSession(session.token, session.expires_at);
      console.log('[Session] 신규 발급:', session.token, '만료:', session.expires_at);
    }

    initSession().finally(() => setReady(true));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!ready) return <View style={{ flex: 1, backgroundColor: '#FFFFFF' }} />;

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack screenOptions={{ headerShown: false }} />
    </ThemeProvider>
  );
}
