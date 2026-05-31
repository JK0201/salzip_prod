// Route: /(onboarding)/diagnosis/step4-budget (Step4: 본인 정보)
import { DiagnosisShell } from '@/components/DiagnosisShell';
import { HOUSEHOLD_TYPES, useDiagnosisStore } from '@/store/useDiagnosisStore';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, Text, TextInput, View } from 'react-native';

export default function Step4BudgetScreen() {
  const {
    age, annualIncomeWan, householdType, homeOwnerless,
    setAge, setAnnualIncomeWan, setHouseholdType, setHomeOwnerless,
  } = useDiagnosisStore();

  const ageNum = parseInt(age, 10);
  const isYouth = !isNaN(ageNum) && ageNum >= 19 && ageNum <= 39;
  const canNext = age.trim().length > 0 && annualIncomeWan.trim().length > 0;

  return (
    <DiagnosisShell
      step={4}
      onBack={() => router.back()}
      onClose={() => router.replace('/(onboarding)/start')}
      footer={
        <Pressable
          className={`w-full rounded-xl py-4 flex-row items-center justify-center gap-2 ${canNext ? 'bg-[#0A0A0B] active:opacity-75' : 'bg-[#E4E4E7]'}`}
          onPress={() => { if (canNext) router.push('/(onboarding)/diagnosis/step5-environment'); }}
          disabled={!canNext}
        >
          <Text className={`text-base font-bold ${canNext ? 'text-white' : 'text-[#A1A1AA]'}`}>진단 시작</Text>
          <Ionicons name="checkmark-circle-outline" size={15} color={canNext ? 'white' : '#A1A1AA'} />
        </Pressable>
      }
    >
      <Text className="text-[22px] font-extrabold leading-[1.3] tracking-[-0.44px] text-[#0A0A0B] mb-2">
        <Text style={{ color: '#059669' }}>마지막</Text>
        {'\n질문이에요!'}
      </Text>
      <Text className="text-[13px] leading-[1.5] text-[#71717A] mb-5">
        {'자격 자동 판정에 필요한\n최소 정보입니다'}
      </Text>

      <View className="flex-1 gap-3">
        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">만 나이</Text>
          <View className="flex-row items-center gap-2 px-3 py-3 bg-white border border-[#E4E4E7] rounded-xl">
            <Ionicons name="person-outline" size={16} color="#A1A1AA" />
            <TextInput
              style={{ flex: 1, fontSize: 14, color: '#18181B' }}
              placeholder="예: 27"
              placeholderTextColor="#A1A1AA"
              value={age}
              onChangeText={(t) => setAge(t.replace(/[^0-9]/g, ''))}
              keyboardType="number-pad"
              maxLength={3}
              returnKeyType="next"
            />
            {isYouth && (
              <Text className="text-[11px] font-bold text-[#059669]">청년</Text>
            )}
          </View>
        </View>

        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">연소득</Text>
          <View className="flex-row items-center gap-2 px-3 py-3 bg-white border border-[#E4E4E7] rounded-xl">
            <Ionicons name="cash-outline" size={16} color="#A1A1AA" />
            <TextInput
              style={{ flex: 1, fontSize: 14, color: '#18181B' }}
              placeholder="예: 4500"
              placeholderTextColor="#A1A1AA"
              value={annualIncomeWan}
              onChangeText={(t) => setAnnualIncomeWan(t.replace(/[^0-9]/g, ''))}
              keyboardType="number-pad"
              maxLength={6}
              returnKeyType="done"
            />
            <Text className="text-[12px] text-[#71717A]">만원</Text>
          </View>
        </View>

        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">가구 형태</Text>
          <View className="flex-row flex-wrap gap-2">
            {HOUSEHOLD_TYPES.map((type) => {
              const sel = householdType === type;
              return (
                <Pressable
                  key={type}
                  onPress={() => setHouseholdType(type)}
                  className={`px-3 py-[7px] rounded-full border ${
                    sel ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'bg-white border-[#E4E4E7]'
                  }`}
                >
                  <Text className={`text-[12px] font-semibold ${sel ? 'text-white' : 'text-[#3F3F46]'}`}>
                    {type}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <Pressable
          className="flex-row items-center justify-between px-3 py-3.5 border border-[#E4E4E7] rounded-xl"
          onPress={() => setHomeOwnerless(!homeOwnerless)}
        >
          <Text className="text-[14px] font-semibold text-[#18181B]">무주택 여부</Text>
          <View
            className="rounded-full justify-center"
            style={{ width: 36, height: 20, backgroundColor: homeOwnerless ? '#0A0A0B' : '#D4D4D8' }}
          >
            <View
              className="absolute bg-white rounded-full"
              style={{ width: 14, height: 14, left: homeOwnerless ? 19 : 3, top: 3 }}
            />
          </View>
        </Pressable>
      </View>

    </DiagnosisShell>
  );
}
