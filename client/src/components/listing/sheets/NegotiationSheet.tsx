// 가격 협상 멘트 생성 시트 (BETA mock).
// 매물 시세·분석 결과 → 임대인 협상 문구 LLM 생성 흉내.
import { useState } from 'react';
import { View, Text, Pressable, Alert } from 'react-native';
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

const TONES = [
  { key: 'polite',     label: '정중하게',  icon: 'happy-outline' as const },
  { key: 'datadriven', label: '근거 위주', icon: 'analytics-outline' as const },
  { key: 'firm',       label: '단호하게',  icon: 'shield-outline' as const },
] as const;
type ToneKey = (typeof TONES)[number]['key'];

const MOCK_BY_TONE: Record<ToneKey, string> = {
  polite: `## 결론
보증금 **300만원 인하** 또는 월세 **5만원 인하**를 정중히 제안하는 멘트입니다. 시세 데이터를 근거로 사용해 임대인과 관계를 해치지 않습니다.

## 추천 멘트

> 안녕하세요, 매물 잘 봤습니다. 위치와 컨디션이 마음에 들어서 계약을 진지하게 고려하고 있어요.
>
> 다만 같은 동네 비슷한 평형 실거래가를 살펴보니 환산보증금 기준 **약 3,500만원 차이**가 있어서, 보증금을 **300만원 인하**해주시면 바로 진행하고 싶습니다.
>
> 어려우시면 월세를 **5만원 조정**해주셔도 좋습니다. 검토 부탁드려요. 감사합니다.

## 활용 팁
- **카카오톡·문자**로 보낼 때 적합한 톤
- 첫 협상 메시지 권장
- 답변 받은 후 추가 협상 여지 충분
`,
  datadriven: `## 결론
**시세 데이터·위험도 점수**를 정량 근거로 제시해 보증금 **500만원 인하**를 요청합니다. 임대인이 거절하기 어려운 근거 중심 톤입니다.

## 추천 멘트

> 안녕하세요. 매물 검토 결과를 공유드립니다.
>
> 1) **동네 중위 환산보증금**: 1억 1,500만원
>    현 매물: 8,000만원 → **3,500만원 저렴** (양호)
>
> 2) **전세가율**: 40.84% (동네 평균)
>    → HUG 보증 가입 가능 등급
>
> 3) **위험도 점수**: 9% (안전)
>
> 다만 입지 분석에서 **마트 0개·약국 적음** 등 인프라 부족 항목이 있어 보증금을 **500만원 인하**해주시면 바로 계약하겠습니다.
>
> 추가 자료 필요하시면 SALZIP 리포트 보내드릴 수 있습니다.

## 활용 팁
- **메일 또는 직접 면담**에 적합
- 분석 리포트 첨부 시 설득력 ↑
- 임대인이 시세 잘 모를 때 효과적
`,
  firm: `## 결론
**확실한 거래 의사 + 명확한 한도**를 제시하는 단호한 톤입니다. 협상이 지지부진할 때 사용합니다.

## 추천 멘트

> 안녕하세요. 매물 결정하려고 합니다.
>
> 시세 분석 결과 보증금 **1억원**까지가 제가 진행 가능한 한도입니다. 이 금액이면 **이번 주 내 계약**하겠습니다.
>
> 그 이상은 시세 대비 무리라고 판단되어 다른 매물을 알아볼 예정입니다. 가능 여부를 **금일 중 회신** 부탁드립니다.

## 활용 팁
- **여러 매물 동시 검토 중**일 때 적합
- 임대인이 가격을 굽히지 않을 때 마지막 카드
- 실제로 다른 옵션이 있을 때만 사용 (블러핑 X)
`,
};

export interface NegotiationSheetProps {
  visible: boolean;
  onClose: () => void;
  listingTitle: string;
}

export function NegotiationSheet({ visible, onClose, listingTitle }: NegotiationSheetProps) {
  const [tone, setTone] = useState<ToneKey>('polite');
  const { text, done } = useMockStream(visible, MOCK_BY_TONE[tone], { chunkSize: 5, delayMs: 14, startDelayMs: 600 });

  return (
    <SheetShell
      visible={visible}
      onClose={onClose}
      icon="chatbubble-ellipses-outline"
      title="가격 협상 멘트 생성"
      sub={listingTitle}
      statusLabel={done ? '완료' : '생성 중'}
      statusColor={done ? '#047857' : '#0A0A0B'}
    >
      {/* 톤 선택 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 12 }}>
        <Text style={{ fontSize: 10, fontWeight: '800', color: NEUTRAL.textMute, letterSpacing: 0.5, marginBottom: 10 }}>
          협상 톤 선택
        </Text>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          {TONES.map((t) => {
            const active = tone === t.key;
            return (
              <Pressable
                key={t.key}
                onPress={() => setTone(t.key)}
                style={{
                  flex: 1, alignItems: 'center', gap: 4,
                  paddingVertical: 10, paddingHorizontal: 6, borderRadius: 8,
                  borderWidth: 1,
                  borderColor: active ? '#0A0A0B' : NEUTRAL.border,
                  backgroundColor: active ? '#0A0A0B' : 'white',
                }}>
                <Ionicons name={t.icon} size={16} color={active ? 'white' : NEUTRAL.ink2} />
                <Text style={{
                  fontSize: 11, fontWeight: '800',
                  color: active ? 'white' : NEUTRAL.ink,
                }}>
                  {t.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* 생성된 멘트 */}
      <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Ionicons name="sparkles" size={12} color={NEUTRAL.ink2} />
            <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.textMute, letterSpacing: 0.5 }}>
              AI 협상 멘트
            </Text>
          </View>
          {done && (
            <Pressable
              onPress={() => Alert.alert('복사됨', '협상 멘트가 클립보드에 복사되었습니다.')}
              style={{ flexDirection: 'row', alignItems: 'center', gap: 4,
                paddingHorizontal: 8, paddingVertical: 4, borderRadius: 6,
                backgroundColor: NEUTRAL.surface }}>
              <Ionicons name="copy-outline" size={11} color={NEUTRAL.ink2} />
              <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.ink2 }}>복사</Text>
            </Pressable>
          )}
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

const MD_STYLES = {
  body: { fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
  heading1: { fontSize: 16, fontWeight: '800' as const, color: NEUTRAL.ink, marginTop: 4, marginBottom: 6 },
  heading2: { fontSize: 14, fontWeight: '800' as const, color: NEUTRAL.ink, marginTop: 10, marginBottom: 4 },
  heading3: { fontSize: 13, fontWeight: '700' as const, color: NEUTRAL.ink, marginTop: 6, marginBottom: 3 },
  strong: { fontWeight: '800' as const, color: NEUTRAL.ink },
  bullet_list: { marginVertical: 4 },
  ordered_list: { marginVertical: 4 },
  list_item: { marginVertical: 2, fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
  paragraph: { marginVertical: 4 },
  blockquote: { backgroundColor: NEUTRAL.surface, borderLeftWidth: 3, borderLeftColor: NEUTRAL.ink, paddingHorizontal: 10, paddingVertical: 6, marginVertical: 6 },
};
