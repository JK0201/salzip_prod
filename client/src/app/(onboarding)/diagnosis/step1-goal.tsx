// Route: /(onboarding)/diagnosis/step1-goal (Step1: 직장·근무지)
import { DiagnosisShell } from '@/components/DiagnosisShell';
import { PostcodeView } from '@/components/PostcodeView';
import { useJobCategories } from '@/hooks/useJobCategories';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Modal, Pressable, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function Step1GoalScreen() {
  const { companyName, workAddress, jobCategoryId, setCompanyName, setWorkAddress, setJobCategory } =
    useDiagnosisStore();
  const [postcodeOpen, setPostcodeOpen] = useState(false);
  const { data: jobCategories, isLoading: jobsLoading, error: jobsError } = useJobCategories();
  const canNext =
    companyName.trim().length > 0 && workAddress.trim().length > 0 && jobCategoryId.length > 0;

  return (
    <DiagnosisShell
      step={1}
      onBack={() => router.back()}
      onClose={() => router.replace('/(onboarding)/start')}
      footer={
        <Pressable
          className={`w-full rounded-xl py-4 flex-row items-center justify-center gap-2 ${canNext ? 'bg-[#0A0A0B] active:opacity-75' : 'bg-[#E4E4E7]'}`}
          onPress={() => { if (canNext) router.push('/(onboarding)/diagnosis/step2-commute'); }}
          disabled={!canNext}
        >
          <Text className={`text-base font-bold ${canNext ? 'text-white' : 'text-[#A1A1AA]'}`}>다음</Text>
          <Ionicons name="arrow-forward" size={15} color={canNext ? 'white' : '#A1A1AA'} />
        </Pressable>
      }
    >
      <Text className="text-[22px] font-extrabold leading-[1.3] tracking-[-0.44px] text-[#0A0A0B] mb-2">
        {'먼저, '}
        <Text style={{ color: '#059669' }}>회사</Text>
        {'는\n어디인가요?'}
      </Text>
      <Text className="text-[13px] leading-[1.5] text-[#71717A] mb-5">
        {'근무지 기준으로\n통근 시간을 계산해요'}
      </Text>

      <View className="flex-1 gap-3">
        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">회사명</Text>
          <View className="flex-row items-center gap-2 px-3 py-3 bg-white border border-[#E4E4E7] rounded-xl">
            <Ionicons name="business-outline" size={16} color="#A1A1AA" />
            <TextInput
              style={{ flex: 1, fontSize: 14, color: '#18181B' }}
              placeholder="예: 카카오, 네이버"
              placeholderTextColor="#A1A1AA"
              value={companyName}
              onChangeText={setCompanyName}
              returnKeyType="next"
            />
          </View>
        </View>

        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">근무지 주소</Text>
          <Pressable
            onPress={() => setPostcodeOpen(true)}
            className="flex-row items-center gap-2 px-3 py-3 bg-white border border-[#E4E4E7] rounded-xl active:opacity-70"
          >
            <Ionicons name="location-outline" size={16} color="#A1A1AA" />
            <Text
              style={{ flex: 1, fontSize: 14, color: workAddress ? '#18181B' : '#A1A1AA' }}
              numberOfLines={1}
            >
              {workAddress || '주소 검색'}
            </Text>
            <Ionicons name="search-outline" size={16} color="#A1A1AA" />
          </Pressable>
        </View>

        <View className="gap-1.5">
          <Text className="text-[12px] font-semibold text-[#3F3F46] tracking-[0.02em]">직종</Text>
          {jobsLoading ? (
            <View className="py-3"><ActivityIndicator size="small" color="#A1A1AA" /></View>
          ) : jobsError ? (
            <Text className="text-[12px] text-[#DC2626] py-2">직종 목록 로드 실패</Text>
          ) : (
            <View className="flex-row flex-wrap gap-2">
              {(jobCategories ?? []).map((cat) => {
                const selected = jobCategoryId === cat.id;
                return (
                  <Pressable
                    key={cat.id}
                    onPress={() => {
                      console.log('[step1] jobCategory selected', cat);
                      setJobCategory(cat.id, cat.name);
                    }}
                    className={`px-3 py-[7px] rounded-full border ${
                      selected ? 'bg-[#0A0A0B] border-[#0A0A0B]' : 'bg-white border-[#E4E4E7]'
                    }`}
                  >
                    <Text className={`text-[12px] font-semibold ${selected ? 'text-white' : 'text-[#3F3F46]'}`}>
                      {cat.name}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          )}
        </View>
      </View>

      <Modal
        visible={postcodeOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setPostcodeOpen(false)}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }} edges={['top']}>
          <View className="h-12 px-3 flex-row items-center justify-between border-b border-[#F4F4F5]">
            <Pressable onPress={() => setPostcodeOpen(false)} hitSlop={12} className="p-1">
              <Ionicons name="close" size={22} color="#0A0A0B" />
            </Pressable>
            <Text className="text-[14px] font-bold text-[#0A0A0B]">근무지 주소 검색</Text>
            <View style={{ width: 24 }} />
          </View>
          <PostcodeView
            onSelect={(result) => {
              const addr = result.roadAddress || result.jibunAddress;
              console.log('[step1] setting workAddress', addr);
              setWorkAddress(addr);
              setPostcodeOpen(false);
            }}
          />
        </SafeAreaView>
      </Modal>
    </DiagnosisShell>
  );
}
