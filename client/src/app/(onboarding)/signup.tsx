// Route: /(onboarding)/signup
import { useState } from 'react';
import { View, Text, Pressable, TextInput, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { signup } from '@/api/session';
import { useSessionStore, SESSION_KEY, SESSION_EXPIRES_KEY, USER_NAME_KEY } from '@/store/useSessionStore';

type Field = 'name' | 'email' | 'password';

function validate(name: string, email: string, password: string): string {
  if (!name.trim()) return '이름을 입력해주세요.';
  if (!email.trim() || !email.includes('@')) return '올바른 이메일을 입력해주세요.';
  if (password.length < 8) return '비밀번호는 8자 이상이어야 해요.';
  return '';
}

export default function SignupScreen() {
  const { from } = useLocalSearchParams<{ from?: string }>();
  const isDiagnosis = from === 'diagnosis';
  const nextRoute = '/(onboarding)/diagnosis/complete';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [focused, setFocused] = useState<Field | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSignup = async () => {
    setError('');
    const msg = validate(name, email, password);
    if (msg) { setError(msg); return; }
    if (!agreed) { setError('서비스 이용약관에 동의해주세요.'); return; }
    setLoading(true);
    try {
      const { token, expires_at, user } = await signup(name.trim(), email.trim(), password);
      if (!token || !expires_at) throw new Error('invalid_response');
      await AsyncStorage.setItem(SESSION_KEY, token);
      await AsyncStorage.setItem(SESSION_EXPIRES_KEY, expires_at);
      if (user?.name) await AsyncStorage.setItem(USER_NAME_KEY, user.name);
      useSessionStore.getState().setSession(token, expires_at);
      useSessionStore.getState().setUserName(user?.name ?? name.trim());
      router.replace(nextRoute as never);
    } catch {
      setError('회원가입에 실패했습니다. 이미 사용 중인 이메일일 수 있어요.');
    } finally {
      setLoading(false);
    }
  };

  const borderColor = (field: Field) => focused === field ? '#0A0A0B' : '#E4E4E7';

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={{ flex: 1 }}
    >
      <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
        <ScrollView
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View className="flex-1 px-6 pt-10 pb-8">

            {/* 타이틀 */}
            {isDiagnosis ? (
              <>
                <Text className="text-[32px] font-extrabold tracking-[-0.64px] text-[#0A0A0B] mb-2">
                  {'진단 완료!\n'}
                  <Text style={{ backgroundColor: '#ECFDF5', color: '#059669' }}>결과</Text>
                  {'를 받아볼까요?'}
                </Text>
                <Text className="text-[14px] text-[#71717A] leading-[1.6] mb-8">
                  {'가입하시면 매칭 동네 Top 5와\n지원사업 자격을 바로 확인할 수 있어요'}
                </Text>
              </>
            ) : (
              <>
                <Text className="text-[28px] font-extrabold tracking-[-0.56px] text-[#0A0A0B] mb-1">
                  계정 만들기
                </Text>
                <Text className="text-[14px] text-[#71717A] mb-8">
                  살집 고민, 지금 시작해볼까요?
                </Text>
              </>
            )}

            {/* 입력 폼 */}
            <View className="gap-4 mb-5">

              {/* 이름 */}
              <View>
                <Text className="text-[13px] font-semibold text-[#0A0A0B] mb-2">이름</Text>
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                  borderColor: borderColor('name'),
                }}>
                  <Ionicons name="person-outline" size={18} color="#A1A1AA" style={{ marginRight: 10 }} />
                  <TextInput
                    value={name}
                    onChangeText={setName}
                    onFocus={() => setFocused('name')}
                    onBlur={() => setFocused(null)}
                    placeholder="이름을 입력하세요"
                    placeholderTextColor="#A1A1AA"
                    autoCorrect={false}
                    style={{ flex: 1, paddingVertical: 14, fontSize: 14, color: '#0A0A0B' }}
                  />
                </View>
              </View>

              {/* 이메일 */}
              <View>
                <Text className="text-[13px] font-semibold text-[#0A0A0B] mb-2">이메일</Text>
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                  borderColor: borderColor('email'),
                }}>
                  <Ionicons name="mail-outline" size={18} color="#A1A1AA" style={{ marginRight: 10 }} />
                  <TextInput
                    value={email}
                    onChangeText={setEmail}
                    onFocus={() => setFocused('email')}
                    onBlur={() => setFocused(null)}
                    placeholder="이메일을 입력하세요"
                    placeholderTextColor="#A1A1AA"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoCorrect={false}
                    style={{ flex: 1, paddingVertical: 14, fontSize: 14, color: '#0A0A0B' }}
                  />
                </View>
              </View>

              {/* 비밀번호 */}
              <View>
                <Text className="text-[13px] font-semibold text-[#0A0A0B] mb-2">
                  {'비밀번호 '}
                  <Text style={{ fontSize: 12, color: '#A1A1AA', fontWeight: '400' }}>(8자 이상)</Text>
                </Text>
                <View style={{
                  flexDirection: 'row', alignItems: 'center',
                  borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                  borderColor: borderColor('password'),
                }}>
                  <Ionicons name="lock-closed-outline" size={18} color="#A1A1AA" style={{ marginRight: 10 }} />
                  <TextInput
                    value={password}
                    onChangeText={setPassword}
                    onFocus={() => setFocused('password')}
                    onBlur={() => setFocused(null)}
                    placeholder="비밀번호를 입력하세요"
                    placeholderTextColor="#A1A1AA"
                    secureTextEntry={!showPw}
                    textContentType="none"
                    autoCapitalize="none"
                    autoCorrect={false}
                    style={{ flex: 1, paddingVertical: 14, fontSize: 14, color: '#0A0A0B' }}
                  />
                  <Pressable onPress={() => setShowPw((v) => !v)} className="pl-2 active:opacity-60">
                    <Ionicons name={showPw ? 'eye-off-outline' : 'eye-outline'} size={18} color="#A1A1AA" />
                  </Pressable>
                </View>
              </View>
            </View>

            {/* 약관 동의 */}
            <Pressable
              onPress={() => setAgreed((v) => !v)}
              className="flex-row items-start gap-2.5 mb-6 active:opacity-70"
            >
              <View style={{
                width: 22, height: 22, borderRadius: 6, marginTop: 1,
                backgroundColor: agreed ? '#059669' : 'white',
                borderWidth: 1.5, borderColor: agreed ? '#059669' : '#D4D4D8',
                alignItems: 'center', justifyContent: 'center',
              }}>
                {agreed && <Ionicons name="checkmark" size={13} color="white" />}
              </View>
              <Text className="flex-1 text-[13px] text-[#18181B] leading-[1.5]">
                <Text className="font-semibold">서비스 이용약관</Text>
                <Text className="text-[#71717A]"> 및 </Text>
                <Text className="font-semibold">개인정보 처리방침</Text>
                <Text className="text-[#71717A]">에 동의합니다</Text>
              </Text>
            </Pressable>

            {/* 에러 */}
            {!!error && (
              <View className="flex-row items-center gap-1.5 mb-3 px-3 py-2.5 bg-[#FEF2F2] rounded-lg">
                <Ionicons name="alert-circle-outline" size={14} color="#EF4444" />
                <Text className="text-[12px] text-[#EF4444] flex-1">{error}</Text>
              </View>
            )}

            {/* 가입 버튼 */}
            <Pressable
              onPress={handleSignup}
              disabled={loading}
              className="w-full bg-[#0A0A0B] rounded-xl py-4 items-center active:opacity-75 mb-6"
            >
              {loading
                ? <ActivityIndicator size="small" color="white" />
                : <Text className="text-white text-base font-bold">
                    {isDiagnosis ? '가입하고 결과 보기' : '가입하기'}
                  </Text>
              }
            </Pressable>

            {/* 로그인 링크 */}
            <View className="flex-row items-center justify-center gap-1">
              <Text className="text-[13px] text-[#71717A]">이미 계정이 있으신가요?</Text>
              <Pressable
                onPress={() => router.push('/(onboarding)/login' as never)}
                className="active:opacity-60"
              >
                <Text className="text-[13px] font-bold text-[#0A0A0B]">로그인</Text>
              </Pressable>
            </View>

          </View>
        </ScrollView>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}
