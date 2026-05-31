// Route: /(onboarding)/diagnosis/step5-environment (Step5: 진단 실행)
import { useEffect, useRef, useState } from 'react';
import { View, Text, Animated } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { postRecommend } from '@/api/recommend';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { useSessionStore } from '@/store/useSessionStore';

const COMMUTE_MINUTES_MAP: Record<string, number> = {
  '30분 이내': 30,
  '45분 이내': 45,
  '1시간 이내': 60,
};

const LABELS = [
  '직장 분석 · 통근 시간',
  '라이프 매칭 · 생활 인프라',
  '안전 검증 · 침수·전세가율',
  '지원사업 자격 자동 판정',
];

const STEP_DELAYS = [0, 800, 1700, 2600, 3500];

function itemState(index: number, step: number): 'done' | 'active' | 'pending' {
  if (index < step) return 'done';
  if (index === step) return 'active';
  return 'pending';
}

export default function Step5EnvironmentScreen() {
  const scale = useRef(new Animated.Value(1)).current;
  const {
    companyName,
    workAddress,
    jobCategoryName,
    commuteLimit,
    lifestyleTags,
    depositWan,
    monthlyRentWan,
    age,
    annualIncomeWan,
    householdType,
    homeOwnerless,
    setResults,
  } = useDiagnosisStore();
  const [step, setStep] = useState(0);

  useEffect(() => {
    const body = {
      workplace_name: companyName,
      workplace_address: workAddress,
      job_type: jobCategoryName,
      max_commute_minutes: COMMUTE_MINUTES_MAP[commuteLimit] ?? 45,
      lifestyle_tags: lifestyleTags.map((t) => t.name),
      deposit_max_wan: depositWan,
      monthly_rent_max_wan: monthlyRentWan,
      age: parseInt(age, 10) || 0,
      annual_income_wan: parseInt(annualIncomeWan, 10) || 0,
      household_type: householdType,
      home_ownerless: homeOwnerless,
    };

    // 로그인 상태면 회원가입 skip → 바로 결과. 비로그인 → signup.
    const { userName, token, isExpired } = useSessionStore.getState();
    const loggedIn = !!userName && !!token && !isExpired();
    const nextRoute = loggedIn
      ? '/(onboarding)/diagnosis/complete'
      : '/(onboarding)/signup?from=diagnosis';

    let navTimer: ReturnType<typeof setTimeout> | null = null;
    const goNext = () => {
      navTimer = setTimeout(() => router.replace(nextRoute as never), 600);
    };

    console.log('[step5] body 전송:', JSON.stringify(body));
    postRecommend(body)
      .then((res) => {
        console.log('[step5] recommend OK areas:', res.areas?.length, 'match:', res.match_id);
        if (res.areas?.length) {
          setResults(res.areas, res.match_id);
          console.log('[step5] setResults 호출됨');
        } else {
          console.log('[step5] areas 비어있음! res:', JSON.stringify(res).slice(0, 200));
        }
      })
      .catch((e) => {
        console.log('[step5] recommend ERROR status:', e?.response?.status, 'data:', JSON.stringify(e?.response?.data), 'msg:', e?.message);
      })
      .finally(goNext);

    Animated.loop(
      Animated.sequence([
        Animated.timing(scale, { toValue: 1.08, duration: 900, useNativeDriver: true }),
        Animated.timing(scale, { toValue: 1, duration: 900, useNativeDriver: true }),
      ])
    ).start();

    const stepTimers = STEP_DELAYS.slice(1).map((delay, i) =>
      setTimeout(() => setStep(i + 1), delay)
    );

    return () => { stepTimers.forEach(clearTimeout); if (navTimer) clearTimeout(navTimer); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <View className="h-9 px-[14px] flex-row items-center justify-center">
        <Text className="text-[13px] font-bold tracking-[-0.13px] text-[#0A0A0B]">진단 중</Text>
      </View>

      <View className="px-4 flex-row items-center gap-2 pt-[14px] mb-[14px]">
        <View className="flex-1 h-[3px] bg-[#10B981] rounded-full" />
        <Text className="text-[9px] font-bold text-[#71717A] tracking-[0.05em]">5 / 5</Text>
      </View>

      <View className="flex-1 px-4 pb-4 items-center justify-center gap-4">
        <Animated.View
          className="w-20 h-20 rounded-full bg-[#ECFDF5] border-2 border-[#10B981] items-center justify-center"
          style={{ transform: [{ scale }] }}
        >
          <Ionicons name="search-outline" size={32} color="#059669" />
        </Animated.View>

        <View className="items-center gap-2">
          <Text className="text-[18px] font-extrabold text-[#0A0A0B] tracking-[-0.36px] text-center">
            {'맞춤 동네를\n찾고 있어요'}
          </Text>
          <Text className="text-[13px] text-[#71717A]">평균 3~5초 소요</Text>
        </View>

        <View className="w-full gap-2.5 mt-2">
          {LABELS.map((label, i) => {
            const state = itemState(i, step);
            return (
              <View key={label} className="flex-row items-center gap-2.5">
                <View className={`w-[18px] h-[18px] rounded-full items-center justify-center ${
                  state === 'done' ? 'bg-[#10B981]'
                  : state === 'active' ? 'bg-[#ECFDF5] border border-[#10B981]'
                  : 'bg-[#E4E4E7]'
                }`}>
                  {state === 'done' && <Ionicons name="checkmark" size={10} color="white" />}
                  {state === 'active' && <View className="w-2 h-2 rounded-full bg-[#10B981]" />}
                </View>
                <Text className={`text-[12px] ${
                  state === 'done' ? 'text-[#0A0A0B] font-medium'
                  : state === 'active' ? 'text-[#059669] font-semibold'
                  : 'text-[#71717A]'
                }`}>
                  {label}
                </Text>
              </View>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
}
