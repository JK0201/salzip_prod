// Route: /(onboarding)/diagnosis/step2-commute (Step2: 통근·라이프스타일)
import { DiagnosisShell } from '@/components/DiagnosisShell';
import { useLifestyleTags } from '@/hooks/useLifestyleTags';
import { COMMUTE_OPTIONS, useDiagnosisStore } from '@/store/useDiagnosisStore';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

export default function Step2CommuteScreen() {
  const { commuteLimit, lifestyleTags, setCommuteLimit, toggleLifestyle } = useDiagnosisStore();
  const { data: tags, isLoading, error } = useLifestyleTags();

  return (
    <DiagnosisShell
      step={2}
      onBack={() => router.back()}
      onClose={() => router.replace('/(onboarding)/start')}
      footer={
        <Pressable
          className="w-full bg-[#0A0A0B] rounded-xl py-4 flex-row items-center justify-center gap-2 active:opacity-75"
          onPress={() => router.push('/(onboarding)/diagnosis/step3-lifestyle')}
        >
          <Text className="text-base font-bold text-white">다음</Text>
          <Ionicons name="arrow-forward" size={15} color="white" />
        </Pressable>
      }
    >
      <Text className="text-[22px] font-extrabold leading-[1.3] tracking-[-0.44px] text-[#0A0A0B] mb-2">
        {'통근 시간,\n어디까지 '}
        <Text style={{ color: '#059669' }}>OK</Text>
        {'인가요?'}
      </Text>
      <Text className="text-[13px] leading-[1.5] text-[#71717A] mb-5">
        선택한 시간 안의 동네만 추천해요
      </Text>

      <View className="flex-1 gap-3">
        <View className="gap-2">
          {COMMUTE_OPTIONS.map((option) => {
            const sel = commuteLimit === option;
            return (
              <Pressable
                key={option}
                onPress={() => setCommuteLimit(option)}
                className={`flex-row items-center justify-between px-4 py-4 rounded-xl bg-white ${
                  sel ? 'border-[1.5px] border-[#0A0A0B]' : 'border border-[#E4E4E7]'
                }`}
              >
                <Text className={`text-[14px] ${sel ? 'font-bold text-[#0A0A0B]' : 'font-medium text-[#18181B]'}`}>
                  {option}
                </Text>
                <View className={`w-[18px] h-[18px] rounded-full border-[1.5px] items-center justify-center ${
                  sel ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'border-[#D4D4D8]'
                }`}>
                  {sel && <View className="w-2 h-2 bg-white rounded-full" />}
                </View>
              </Pressable>
            );
          })}
        </View>

        <View className="gap-2 mt-1">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">
            라이프스타일 <Text className="text-[#A1A1AA] font-normal">· 복수 선택</Text>
          </Text>
          {isLoading ? (
            <View className="py-3"><ActivityIndicator size="small" color="#A1A1AA" /></View>
          ) : error ? (
            <Text className="text-[12px] text-[#DC2626] py-2">라이프스타일 태그 로드 실패</Text>
          ) : (
            <View className="flex-row flex-wrap gap-2">
              {(tags ?? []).map((tag) => {
                const sel = lifestyleTags.some((t) => t.id === tag.id);
                return (
                  <Pressable
                    key={tag.id}
                    onPress={() => {
                      console.log('[step2] lifestyle toggle', tag);
                      toggleLifestyle(tag);
                    }}
                    className={`px-3 py-[7px] rounded-full border ${
                      sel ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'bg-white border-[#E4E4E7]'
                    }`}
                  >
                    <Text className={`text-[12px] font-semibold ${sel ? 'text-white' : 'text-[#3F3F46]'}`}>
                      {tag.name}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
        </View>
      </View>

    </DiagnosisShell>
  );
}
