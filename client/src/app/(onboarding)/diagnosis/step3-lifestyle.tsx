// Route: /(onboarding)/diagnosis/step3-lifestyle (Step3: 예산)
import { DiagnosisShell } from '@/components/DiagnosisShell';
import { usePoliciesPreview } from '@/hooks/usePoliciesPreview';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useRef } from 'react';
import { ActivityIndicator, PanResponder, Pressable, Text, View } from 'react-native';

const DEPOSIT_MAX = 10000;
const DEPOSIT_STEP = 500;
const RENT_MAX = 100;
const RENT_STEP = 5;

function DragSlider({ value, min, max, step, onChange, label, rangeMaxLabel, displayValue }: {
  value: number; min: number; max: number; step: number;
  onChange: (v: number) => void;
  label: string; rangeMaxLabel: string; displayValue: string;
}) {
  const trackWidthRef = useRef(0);
  const startPercentRef = useRef(0);
  const percent = (value - min) / (max - min);

  const snap = (ratio: number) => {
    const clamped = Math.max(0, Math.min(1, ratio));
    return Math.max(min, Math.min(max, Math.round((min + clamped * (max - min)) / step) * step));
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        const ratio = evt.nativeEvent.locationX / trackWidthRef.current;
        startPercentRef.current = Math.max(0, Math.min(1, ratio));
        onChange(snap(ratio));
      },
      onPanResponderMove: (_, g) => {
        onChange(snap(startPercentRef.current + g.dx / trackWidthRef.current));
      },
    })
  ).current;

  return (
    <View style={{ gap: 8 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <Text style={{ fontSize: 12, fontWeight: '600', color: '#3F3F46' }}>{label}</Text>
        <Text style={{ fontSize: 15, fontWeight: '800', color: '#0A0A0B', letterSpacing: -0.15 }}>
          {displayValue}
        </Text>
      </View>

      {/* 터치 영역 (thumb 고려해 위아래 여유 포함) */}
      <View
        style={{ height: 28, position: 'relative' }}
        onLayout={(e) => { trackWidthRef.current = e.nativeEvent.layout.width; }}
        {...panResponder.panHandlers}
      >
        {/* 트랙 */}
        <View style={{
          position: 'absolute', left: 0, right: 0, top: 11, height: 6,
          borderRadius: 3, backgroundColor: '#E4E4E7', overflow: 'hidden',
        }}>
          <View style={{
            position: 'absolute', top: 0, left: 0, bottom: 0,
            width: `${percent * 100}%`,
            backgroundColor: '#0A0A0B', borderRadius: 3,
          }} />
        </View>

        {/* 썸 */}
        <View style={{
          position: 'absolute',
          width: 22, height: 22, borderRadius: 11,
          backgroundColor: 'white',
          borderWidth: 2.5, borderColor: '#0A0A0B',
          left: `${percent * 100}%`,
          marginLeft: -11,
          top: 3,
          shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, elevation: 3,
        }} />
      </View>

      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={{ fontSize: 10, color: '#A1A1AA' }}>0</Text>
        <Text style={{ fontSize: 10, color: '#A1A1AA' }}>{rangeMaxLabel}</Text>
      </View>
    </View>
  );
}

function HintCard({
  text,
  sub,
  active,
  loading,
}: {
  text: string;
  sub?: string | null;
  active: boolean;
  loading?: boolean;
}) {
  return (
    <View style={{
      flexDirection: 'row', alignItems: sub ? 'flex-start' : 'center', gap: 8,
      paddingHorizontal: 12, paddingVertical: 12, borderRadius: 12, borderWidth: 1,
      backgroundColor: active ? '#ECFDF5' : '#FAFAFA',
      borderColor: active ? '#D1FAE5' : '#E4E4E7',
      opacity: loading ? 0.65 : 1,
    }}>
      {loading ? (
        <ActivityIndicator
          size="small"
          color={active ? '#059669' : '#A1A1AA'}
          style={{ width: 14, height: 14, marginTop: sub ? 2 : 0 }}
        />
      ) : (
        <Ionicons
          name={active ? 'checkmark' : 'close'}
          size={14}
          color={active ? '#059669' : '#A1A1AA'}
          style={{ marginTop: sub ? 2 : 0 }}
        />
      )}
      <View style={{ flex: 1, gap: 3 }}>
        <Text style={{ fontSize: 12, fontWeight: '600', color: active ? '#059669' : '#A1A1AA' }}>
          {text}
        </Text>
        {sub ? (
          <Text style={{ fontSize: 11, color: active ? '#047857' : '#71717A' }} numberOfLines={1}>
            {sub}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

function formatLoan(v: number): string {
  return v >= 10000
    ? `${(v / 10000).toFixed(v % 10000 === 0 ? 0 : 1)}억`
    : `${v.toLocaleString()}만`;
}

function namesSub(items: { name: string }[]): string | null {
  if (items.length === 0) return null;
  if (items.length === 1) return items[0].name;
  if (items.length === 2) return `${items[0].name}, ${items[1].name}`;
  return `${items[0].name}, ${items[1].name} 외 ${items.length - 2}건`;
}

export default function Step3LifestyleScreen() {
  const { depositWan, monthlyRentWan, setDepositWan, setMonthlyRentWan } = useDiagnosisStore();
  const { data: policies, isLoading: policiesLoading } = usePoliciesPreview(depositWan, monthlyRentWan);

  const depositDisplay =
    depositWan >= 10000 ? `${depositWan / 10000}억` : `${depositWan.toLocaleString()}만`;
  const rentDisplay = `${monthlyRentWan}만`;

  const monthlyItems = policies?.by_card.monthly ?? [];
  const jeonseItems = policies?.by_card.jeonse ?? [];
  const monthlyCount = monthlyItems.length;
  const jeonseCount = jeonseItems.length;
  const maxMonthly = policies?.summary.max_monthly_support_wan ?? null;
  const maxLoan = policies?.summary.max_loan_limit_wan ?? null;

  return (
    <DiagnosisShell
      step={3}
      onBack={() => router.back()}
      onClose={() => router.replace('/(onboarding)/start')}
      footer={
        <Pressable
          className="w-full bg-[#0A0A0B] rounded-xl py-4 flex-row items-center justify-center gap-2 active:opacity-75"
          onPress={() => router.push('/(onboarding)/diagnosis/step4-budget')}
        >
          <Text className="text-base font-bold text-white">다음</Text>
          <Ionicons name="arrow-forward" size={15} color="white" />
        </Pressable>
      }
    >
      <Text className="text-[22px] font-extrabold leading-[1.3] tracking-[-0.44px] text-[#0A0A0B] mb-2">
        <Text style={{ color: '#059669' }}>예산</Text>
        {'은\n어느 정도인가요?'}
      </Text>
      <Text className="text-[13px] leading-[1.5] text-[#71717A] mb-5">
        {'청년 지원사업 한도와\n자동으로 매칭해드려요'}
      </Text>

      <View className="flex-1 gap-5">
        <DragSlider
          label="보증금"
          value={depositWan}
          min={0}
          max={DEPOSIT_MAX}
          step={DEPOSIT_STEP}
          onChange={setDepositWan}
          displayValue={depositDisplay}
          rangeMaxLabel="1억"
        />
        <DragSlider
          label="월세"
          value={monthlyRentWan}
          min={0}
          max={RENT_MAX}
          step={RENT_STEP}
          onChange={setMonthlyRentWan}
          displayValue={rentDisplay}
          rangeMaxLabel="100만"
        />
        <HintCard
          active={monthlyCount > 0}
          loading={policiesLoading}
          text={
            monthlyCount > 0
              ? `월세 지원 ${monthlyCount}건 매칭${maxMonthly !== null ? ` · 최대 월 ${maxMonthly}만` : ''}`
              : '월세 지원 매칭 없음'
          }
          sub={namesSub(monthlyItems)}
        />
        <HintCard
          active={jeonseCount > 0}
          loading={policiesLoading}
          text={
            jeonseCount > 0
              ? `전세 대출 ${jeonseCount}건 매칭${maxLoan !== null ? ` · 최대 한도 ${formatLoan(maxLoan)}` : ''}`
              : '전세 대출 매칭 없음'
          }
          sub={namesSub(jeonseItems)}
        />
      </View>

    </DiagnosisShell>
  );
}
