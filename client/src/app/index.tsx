// Route: / (시작 - 로그인 여부로 분기)
import { useEffect, useState } from 'react';
import { Redirect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SESSION_KEY, SESSION_EXPIRES_KEY, USER_NAME_KEY } from '@/store/useSessionStore';

export default function Index() {
  const [dest, setDest] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const token = await AsyncStorage.getItem(SESSION_KEY);
      const name = await AsyncStorage.getItem(USER_NAME_KEY);
      const exp = await AsyncStorage.getItem(SESSION_EXPIRES_KEY);
      const valid = !!token && !!exp && new Date(exp) > new Date();
      // 로그인(이름 + 유효 토큰) → 메인, 아니면 온보딩
      setDest(name && valid ? '/(main)/hsubsidy' : '/(onboarding)/start');
    })();
  }, []);

  if (!dest) return null; // AsyncStorage 읽는 동안 로딩
  return <Redirect href={dest as never} />;
}
