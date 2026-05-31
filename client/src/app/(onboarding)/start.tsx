import { View, Text, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const CARDS = [
  {
    icon: 'business-outline' as const,
    title: '직장·라이프·안전 매칭',
    desc: '출퇴근 30분 + 야간 활기 + 침수 안전',
  },
  {
    icon: 'checkmark-circle-outline' as const,
    title: '지원사업 자격 자동 진단',
    desc: '청년월세·버팀목·HUG 보증 한 번에',
  },
  {
    icon: 'shield-checkmark-outline' as const,
    title: '깡통전세 사전 경고',
    desc: '전세가율·침수이력 + 보증가능 매물 우선',
  },
] as const;

export default function StartScreen() {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      <View className="flex-1 px-6 pb-8">

        {/* 브랜드 마크 */}
        <View className="flex-row items-center gap-2 mt-4 mb-12">
          <View className="w-8 h-8 bg-[#0A0A0B] rounded-lg overflow-hidden">
            <View className="absolute top-1.5 left-1.5 w-3.5 h-3.5 bg-[#10B981] rounded-full" />
            <View className="absolute bottom-1.5 right-1.5 w-1.5 h-1.5 bg-white rounded-full" />
          </View>
          <Text className="text-[17px] font-bold tracking-[-0.34px] text-[#0A0A0B]">
            살집고민끝
          </Text>
        </View>

        {/* 히어로 */}
        <Text className="text-[32px] font-extrabold leading-10 tracking-[-0.81px] text-[#0A0A0B] mb-3">
          {'청년월세 받았는데,\n'}
          <Text style={{ color: '#059669', backgroundColor: '#D1FAE5', borderRadius: 4 }}>
            어디서 살지
          </Text>
          {'?'}
        </Text>

        <Text className="text-[15px] leading-[22px] text-[#71717A] mb-8">
          {'5분이면 끝나는 청년 주거 큐레이션.\n직장 · 라이프 · 안전을 한 번에 진단해드려요.'}
        </Text>

        {/* 가치 카드 */}
        <View className="flex-1 gap-3 pb-6">
          {CARDS.map(({ icon, title, desc }) => (
            <View
              key={title}
              className="flex-row items-center gap-[14px] p-4 bg-white border border-[#E4E4E7] rounded-xl"
            >
              <View className="w-11 h-11 bg-[#ECFDF5] rounded-[10px] items-center justify-center">
                <Ionicons name={icon} size={22} color="#059669" />
              </View>
              <View className="flex-1">
                <Text className="text-sm font-bold leading-5 text-[#0A0A0B] mb-0.5">
                  {title}
                </Text>
                <Text className="text-xs leading-[17px] text-[#71717A]">
                  {desc}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color="#A1A1AA" />
            </View>
          ))}
        </View>

        {/* CTA */}
        <View className="gap-3">
          <Pressable
            className="w-full bg-[#0A0A0B] rounded-xl py-4 flex-row items-center justify-center gap-2 active:opacity-75"
            onPress={() => router.push('/(onboarding)/diagnosis/step1-goal')}
          >
            <Text className="text-white text-base font-bold tracking-[-0.19px]">
              5분 진단 시작하기
            </Text>
            <Ionicons name="arrow-forward" size={18} color="white" />
          </Pressable>

          <View className="flex-row items-center justify-center gap-1.5">
            <View className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
            <Text className="text-xs text-[#71717A]">이미 진단하셨다면</Text>
            <Pressable onPress={() => router.push('/(onboarding)/login' as never)}>
              <Text className="text-xs font-semibold text-[#0A0A0B] border-b border-[#E4E4E7]">
                로그인
              </Text>
            </Pressable>
          </View>
        </View>

      </View>
    </SafeAreaView>
  );
}
