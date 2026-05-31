// 계약서 위험 조항 분석 시트 (BETA mock).
// 업로드된 계약서 텍스트 → LLM이 독소·사기 조항 탐지하는 흉내.
import { View, Text, Pressable } from 'react-native';
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

const STEPS = [
  '계약서 OCR 텍스트 추출 중...',
  '표준 임대차계약서 양식 대조 중...',
  '특약 조항 의미 분석 중...',
  '독소·사기 패턴 매칭 중...',
  '조항별 위험도 산출 중...',
];

const MOCK_REPORT = `## 결론
**6개 조항 검토 완료 · 위험 조항 2건 발견**. 특약 3조와 4조는 임차인에게 불리한 표현이 포함되어 있어 협의가 필요합니다.

## 위험 조항

| 조항 | 위험도 | 내용 요약 |
|---|---|---|
| 특약 제3조 | 🔴 높음 | 보증금 반환 시기를 "임대인 사정에 따라 협의"로 명시 — 반환 지연 분쟁 소지 |
| 특약 제4조 | 🟡 주의 | 원상복구 범위가 "사용 흔적 일체"로 광범위 — 통상 손모 청구 가능성 |
| 제7조 (수선) | 🟢 안전 | 표준 양식과 일치 |
| 제8조 (해지) | 🟢 안전 | 위약금 조항 적정 |
| 확정일자 | ⚠ 누락 | 계약서상 확정일자 받기 의무 명시 없음 — 별도 확인 필요 |
| 전입신고 | 🟢 안전 | 임대인 동의 조항 포함 |

## 권장 수정 문구

### 특약 제3조 (보증금 반환)
> "임대인은 계약 종료일로부터 **30일 이내** 보증금을 반환한다. 반환 지연 시 연 **5%** 이자를 가산한다."

### 특약 제4조 (원상복구)
> "임차인의 원상복구 의무는 **통상의 사용에 따른 자연 손모를 제외**한 임차인 귀책 사유에 한한다."

## 추가 권장 조치
1. **확정일자** — 잔금일 당일 동주민센터에서 반드시 받기
2. **전입신고** — 입주 즉시 (대항력 발생)
3. **등기부등본** — 잔금 전일·당일 재확인 (가압류 신규 등재 체크)

> 실제 계약 체결 전 변호사·공인중개사 검토를 권장합니다.
`;

export interface ContractSheetProps {
  visible: boolean;
  onClose: () => void;
}

export function ContractSheet({ visible, onClose }: ContractSheetProps) {
  const { text, done } = useMockStream(visible, MOCK_REPORT, { chunkSize: 5, delayMs: 14, startDelayMs: 1500 });

  return (
    <SheetShell
      visible={visible}
      onClose={onClose}
      icon="document-text-outline"
      title="계약서 위험 조항 분석"
      sub="독소·사기 조항 자동 탐지"
      statusLabel={done ? '완료' : '분석 중'}
      statusColor={done ? '#047857' : '#0A0A0B'}
    >
      {/* 업로드 미리보기 — mock */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 12 }}>
        <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 10 }}>
          업로드된 계약서
        </Text>
        <View style={{
          flexDirection: 'row', alignItems: 'center', gap: 10,
          padding: 10, borderRadius: 8, borderWidth: 1, borderColor: NEUTRAL.borderFaint,
        }}>
          <View style={{ width: 36, height: 44, borderRadius: 4, backgroundColor: '#FEE2E2',
            alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="document-text" size={18} color="#B91C1C" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 12, fontWeight: '700', color: NEUTRAL.ink }} numberOfLines={1}>
              주택임대차계약서_2026.pdf
            </Text>
            <Text style={{ fontSize: 10, color: NEUTRAL.textMute, marginTop: 2 }}>
              3페이지 · 약 1,840자 · 특약 5건
            </Text>
          </View>
          <Pressable style={{ paddingHorizontal: 8, paddingVertical: 6, opacity: 0.5 }}>
            <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.ink }}>교체</Text>
          </Pressable>
        </View>
      </View>

      {/* 진행 스텝퍼 */}
      <StepperList visible={visible} done={done} />

      {/* 마크다운 분석 결과 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginTop: 12 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 }}>
          <Ionicons name="sparkles" size={12} color={NEUTRAL.ink2} />
          <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.textMute, letterSpacing: 0.5 }}>
            AI 조항 분석
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
  const { text: revealedRaw } = useMockStream(visible, STEPS.join('\n'), {
    chunkSize: 200, delayMs: 240, startDelayMs: 200,
  });
  const revealed = revealedRaw.split('\n').filter(Boolean);

  return (
    <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14 }}>
      <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 10 }}>
        분석 프로세스
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
