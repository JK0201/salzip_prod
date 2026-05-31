// 임대인 신뢰도 리포트 시트 (BETA mock).
// 마크다운 mock 스트리밍 — 멀티에이전트 분석 흉내.
import { View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Markdown from 'react-native-markdown-display';
import { SheetShell } from './SheetShell';
import { useMockStream } from '@/hooks/useMockStream';

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  border: '#E4E4E7',
  borderFaint: '#F4F4F5',
  surface: '#FAFAFA',
};

const MOCK_REPORT = `## 결론
**신뢰도 82점 · 안전 등급**. 보증사고 이력이 없고 HUG 가입이 가능한 임대인입니다. 기본 검증 5종은 모두 통과했습니다.

## 검증 항목

| 항목 | 결과 | 비고 |
|---|---|---|
| HUG 보증사고 이력 | ✅ 0건 | 최근 5년 |
| 대법원 등기 변동 | ✅ 안정 | 소유권 5년 유지 |
| 세금 체납 등재 | ✅ 없음 | 국세청 공시 기준 |
| 다주택 보유 현황 | ⚠ 7채 | 주의 임계치 (10채) 미만 |
| 임차인 분쟁 검색 | ✅ 미발견 | 공개 판례 검색 |

## 강점
- **장기 보유** — 해당 매물을 5년 이상 보유하여 매도 가능성이 낮습니다.
- **HUG 가입 가능** — 보증보험으로 보증금 회수 안전망 확보 가능합니다.
- **체납·분쟁 무관** — 공시 정보 기준 법적 리스크 신호 없음.

## 주의
- **다주택 보유 7채** — 갭투자 가능성을 완전히 배제할 수 없습니다. 임대 사업 규모를 추가 확인하십시오.
- 본 리포트는 **공개 데이터**(HUG·등기·국세청·판례) 기반이며, 비공개 분쟁·구두 합의는 포함되지 않습니다.

## 계약 전 추가 확인 권장
1. **등기부등본** 직접 발급 — 가압류·근저당 실시간 확인
2. **국세완납증명서** 요구 — 임대인 발급분 수령
3. **HUG 보증보험** 동시 신청 — 보증금 반환 안전망

> 공개 데이터 기반 분석이며, 최종 의사결정 전 전문가 상담을 권장합니다.
`;

const STEPS = [
  '임대인 식별 정보 조회 중...',
  'HUG 보증사고 이력 검색 중...',
  '대법원 등기 변동 분석 중...',
  '국세청 체납 공시 대조 중...',
  '판례·분쟁 키워드 매칭 중...',
  '5종 항목 종합 점수 산출 중...',
];

export interface LandlordSheetProps {
  visible: boolean;
  onClose: () => void;
  ownerLabel: string;     // ex) "임대인 김O O"
}

export function LandlordSheet({ visible, onClose, ownerLabel }: LandlordSheetProps) {
  const { text, done } = useMockStream(visible, MOCK_REPORT, { chunkSize: 5, delayMs: 14, startDelayMs: 1400 });

  return (
    <SheetShell
      visible={visible}
      onClose={onClose}
      icon="person-circle-outline"
      title="임대인 신뢰도 리포트"
      sub={ownerLabel}
      statusLabel={done ? '완료' : '분석 중'}
      statusColor={done ? '#047857' : '#0A0A0B'}
    >
      {/* 진행 스텝퍼 — 멀티에이전트 검색 흉내 */}
      <StepperList visible={visible} done={done} />

      {/* 마크다운 리포트 — 스트리밍 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginTop: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 }}>
          <Ionicons name="sparkles" size={12} color={NEUTRAL.ink2} />
          <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.textMute, letterSpacing: 0.5 }}>
            AI 신뢰도 분석
          </Text>
        </View>
        {text ? (
          <Markdown style={MD_STYLES}>{text}</Markdown>
        ) : (
          <Text style={{ fontSize: 13, color: NEUTRAL.textMute }}>대기 중...</Text>
        )}
        {!done && text.length > 0 && (
          <Text style={{ fontSize: 13, color: NEUTRAL.ink, marginTop: 2 }}> ▎</Text>
        )}
      </View>
    </SheetShell>
  );
}

function StepperList({ visible, done }: { visible: boolean; done: boolean }) {
  // 스텝 순차 활성. visible 시점부터 200ms 간격으로 1개씩.
  const { text: revealedRaw } = useMockStream(visible, STEPS.join('\n'), {
    chunkSize: 200, delayMs: 220, startDelayMs: 200,
  });
  const revealed = revealedRaw.split('\n').filter(Boolean);

  return (
    <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14 }}>
      <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 10 }}>
        검증 프로세스
      </Text>
      <View style={{ gap: 6 }}>
        {STEPS.map((s, i) => {
          const reached = revealed.length > i || done;
          const active = reached && (revealed.length === i + 1) && !done;
          return (
            <View key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Ionicons
                name={reached && !active ? 'checkmark-circle' : active ? 'ellipsis-horizontal-circle' : 'ellipse-outline'}
                size={14}
                color={reached && !active ? '#047857' : active ? '#0A0A0B' : '#D4D4D8'}
              />
              <Text style={{
                fontSize: 12,
                color: reached ? NEUTRAL.text : NEUTRAL.textMute,
                fontWeight: active ? '700' : '500',
                flex: 1,
              }}>
                {s.replace(' 중...', reached && !active ? ' 완료' : ' 중...')}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const MD_STYLES = {
  body: { fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
  heading1: { fontSize: 16, fontWeight: '800' as const, color: NEUTRAL.ink, marginTop: 4, marginBottom: 6 },
  heading2: { fontSize: 14, fontWeight: '800' as const, color: NEUTRAL.ink, marginTop: 10, marginBottom: 4 },
  heading3: { fontSize: 13, fontWeight: '700' as const, color: NEUTRAL.ink, marginTop: 6, marginBottom: 3 },
  strong: { fontWeight: '800' as const, color: NEUTRAL.ink },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2, fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
  table: { borderWidth: 1, borderColor: NEUTRAL.border, borderRadius: 6, marginVertical: 8 },
  thead: { backgroundColor: NEUTRAL.surface },
  th: { padding: 8, fontWeight: '700' as const, fontSize: 12, color: NEUTRAL.ink, borderRightWidth: 1, borderColor: NEUTRAL.border },
  td: { padding: 8, fontSize: 12, color: NEUTRAL.text, borderTopWidth: 1, borderRightWidth: 1, borderColor: NEUTRAL.border },
  paragraph: { marginVertical: 4 },
  blockquote: { backgroundColor: NEUTRAL.surface, borderLeftWidth: 3, borderLeftColor: NEUTRAL.ink, paddingHorizontal: 10, paddingVertical: 6, marginVertical: 6 },
};
