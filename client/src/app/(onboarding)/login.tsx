// Route: /(onboarding)/login
import { login } from '@/api/session';
import { SESSION_EXPIRES_KEY, SESSION_KEY, USER_NAME_KEY, useSessionStore } from '@/store/useSessionStore';
import { useFavoriteStore } from '@/store/useFavoriteStore';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function LoginScreen() {
  const { from } = useLocalSearchParams<{ from?: string }>();
  const nextRoute = '/(onboarding)/diagnosis/complete';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [focused, setFocused] = useState<'email' | 'password' | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError('');
    if (!email.trim() || !password) {
      setError('이메일과 비밀번호를 모두 입력해주세요.');
      return;
    }
    setLoading(true);
    try {
      const res = await login(email.trim(), password);
      console.log('[login] response:', JSON.stringify(res));
      const { token, expires_at, user } = res;
      if (!token || !expires_at) {
        console.warn('[login] invalid_response - token:', token, 'expires_at:', expires_at);
        throw new Error('invalid_response');
      }
      await AsyncStorage.setItem(SESSION_KEY, token);
      await AsyncStorage.setItem(SESSION_EXPIRES_KEY, expires_at);
      if (user?.name) await AsyncStorage.setItem(USER_NAME_KEY, user.name);
      useSessionStore.getState().setSession(token, expires_at);
      useSessionStore.getState().setUserName(user?.name ?? null);
      useFavoriteStore.getState().load();
      router.replace(nextRoute as never);
    } catch (e) {
      const err = e as { message?: string; response?: { status: number; data: unknown } };
      console.error('[login] error:', err?.message, err?.response?.status, JSON.stringify(err?.response?.data));
      setError('이메일 또는 비밀번호가 올바르지 않습니다.');
    } finally {
      setLoading(false);
    }
  };

  const inputBorder = (field: 'email' | 'password') =>
    focused === field ? '#0A0A0B' : '#E4E4E7';

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View className="flex-1 px-6 pb-8">

            {/* 뒤로가기 */}
            <Pressable
              onPress={() => router.back()}
              className="mt-4 mb-10 w-9 h-9 items-center justify-center -ml-1 active:opacity-60"
            >
              <Ionicons name="arrow-back" size={22} color="#0A0A0B" />
            </Pressable>

            {/* 타이틀 */}
            <Text className="text-[28px] font-extrabold tracking-[-0.56px] text-[#0A0A0B] mb-2">
              다시 만났어요!
            </Text>
            <Text className="text-[14px] text-[#71717A] leading-[1.6] mb-8">
              {'계속하려면 '}
              <Text style={{ backgroundColor: '#ECFDF5', color: '#059669' }}>로그인</Text>
              {'해주세요'}
            </Text>

            {/* 입력 폼 */}
            <View className="gap-4 mb-2">
              <View>
                <Text className="text-[13px] font-semibold text-[#0A0A0B] mb-2">이메일</Text>
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                  borderColor: inputBorder('email'),
                }}>
                  <Ionicons name="mail-outline" size={18} color="#A1A1AA" style={{ marginRight: 10 }} />
                  <TextInput
                    value={email}
                    onChangeText={setEmail}
                    onFocus={() => setFocused('email')}
                    onBlur={() => setFocused(null)}
                    onSubmitEditing={handleLogin}
                    placeholder="이메일을 입력하세요"
                    placeholderTextColor="#A1A1AA"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="next"
                    style={{ flex: 1, paddingVertical: 14, fontSize: 14, color: '#0A0A0B' }}
                  />
                </View>
              </View>

              <View>
                <Text className="text-[13px] font-semibold text-[#0A0A0B] mb-2">비밀번호</Text>
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                  borderColor: inputBorder('password'),
                }}>
                  <Ionicons name="lock-closed-outline" size={18} color="#A1A1AA" style={{ marginRight: 10 }} />
                  <TextInput
                    value={password}
                    onChangeText={setPassword}
                    onFocus={() => setFocused('password')}
                    onBlur={() => setFocused(null)}
                    onSubmitEditing={handleLogin}
                    placeholder="비밀번호를 입력하세요"
                    placeholderTextColor="#A1A1AA"
                    secureTextEntry={!showPw}
                    textContentType="password"
                    autoCapitalize="none"
                    autoCorrect={false}
                    returnKeyType="done"
                    style={{ flex: 1, paddingVertical: 14, fontSize: 14, color: '#0A0A0B' }}
                  />
                  <Pressable onPress={() => setShowPw((v) => !v)} className="pl-2 active:opacity-60">
                    <Ionicons name={showPw ? 'eye-off-outline' : 'eye-outline'} size={18} color="#A1A1AA" />
                  </Pressable>
                </View>
              </View>
            </View>

            {/* 비밀번호 찾기 */}
            <Pressable className="self-end mb-6 mt-1 active:opacity-60">
              <Text className="text-[12px] text-[#A1A1AA]">비밀번호를 잊으셨나요?</Text>
            </Pressable>

            {/* 에러 */}
            {!!error && (
              <View className="flex-row items-center gap-1.5 mb-3 px-3 py-2.5 bg-[#FEF2F2] rounded-lg">
                <Ionicons name="alert-circle-outline" size={14} color="#EF4444" />
                <Text className="text-[12px] text-[#EF4444] flex-1">{error}</Text>
              </View>
            )}

            {/* 로그인 버튼 */}
            <Pressable
              onPress={handleLogin}
              disabled={loading}
              className="w-full bg-[#0A0A0B] rounded-xl py-4 items-center active:opacity-75 mb-5"
            >
              {loading
                ? <ActivityIndicator size="small" color="white" />
                : <Text className="text-white text-base font-bold">로그인</Text>
              }
            </Pressable>

            {/* 구분선 */}
            <View className="flex-row items-center gap-3 mb-5">
              <View className="flex-1 h-px bg-[#F4F4F5]" />
              <Text className="text-[11px] text-[#A1A1AA] font-medium">또는 소셜 로그인</Text>
              <View className="flex-1 h-px bg-[#F4F4F5]" />
            </View>

            {/* 소셜 로그인 */}
            <View className="gap-2.5 mb-8">
              <Pressable
                onPress={() => { /* TODO: 카카오 OAuth 후 router.replace(nextRoute) */ }}
                className="w-full rounded-xl py-[13px] flex-row items-center justify-center gap-2 active:opacity-75"
                style={{ backgroundColor: '#FEE500', borderRadius: 12 }}
              >
                <Text style={{ fontSize: 15, lineHeight: 18 }}>💬</Text>
                <Text style={{ fontSize: 14, fontWeight: '700', color: '#3A1D1D' }}>
                  카카오로 계속하기
                </Text>
              </Pressable>

              <Pressable
                onPress={() => { /* TODO: Apple Sign-In 후 router.replace(nextRoute) */ }}
                className="w-full rounded-xl py-[13px] flex-row items-center justify-center gap-2 active:opacity-75"
                style={{ borderWidth: 1, borderColor: '#E4E4E7', borderRadius: 12 }}
              >
                <Ionicons name="logo-apple" size={16} color="#0A0A0B" />
                <Text style={{ fontSize: 14, fontWeight: '700', color: '#0A0A0B' }}>Apple로 계속하기</Text>
              </Pressable>
            </View>

            {/* 회원가입 링크
            <View className="flex-row items-center justify-center gap-1">
              <Text className="text-[13px] text-[#71717A]">계정이 없으신가요?</Text>
              <Pressable
                onPress={() => router.push(`/(onboarding)/signup${from ? `?from=${from}` : ''}` as never)}
                className="active:opacity-60"
              >
                <Text className="text-[13px] font-bold text-[#0A0A0B]">회원가입</Text>
              </Pressable>
            </View> */}

          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
