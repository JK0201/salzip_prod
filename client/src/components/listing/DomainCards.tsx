// 매물 상세 — 5 도메인 패널
// 종합(synth) = 히어로 카드 (LLM 텍스트 직접 흐름)
// 4 도메인(risk/sise/locale/support) = 2x2 미니 그리드 (점수만, 탭 → 디테일 시트)
import { useMemo } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Markdown from 'react-native-markdown-display';
import type { AgentName, ScoresPayload } from '@/api/analyze';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';

export type Status = 'idle' | 'streaming' | 'done' | 'error';

// 컬러 정책: 도메인 구분은 아이콘+라벨로, 색은 모노크롬. tone(safe/warn/danger)은 "평가"에만 사용.
const DOMAIN: Record<
  AgentName,
  { title: string; icon: keyof typeof Ionicons.glyphMap }
> = {
  synth:   { title: 'AI 종합 결론', icon: 'sparkles' },
  risk:    { title: '위험',         icon: 'shield-checkmark-outline' },
  sise:    { title: '시세',         icon: 'pricetag-outline' },
  locale:  { title: '입지',         icon: 'location-outline' },
  support: { title: '지원사업',     icon: 'cash-outline' },
};

// 사용자 lifestyle_tag → 인프라 카테고리 매핑
const TAG_TO_CATEGORY: Record<string, string> = {
  '식도락': 'food',
  '카페 라이프': 'cafe',
  '산책': 'park',
  '문화·여가': 'culture',
  '장보기 편함': 'mart',
  '역세권': 'subway',
  '의료 가까이': 'hospital',
};

const CATEGORY_LABELS: Record<string, string> = {
  cafe: '카페', food: '음식점', culture: '문화', park: '공원',
  mart: '마트', subway: '지하철', hospital: '병원', pharmacy: '약국',
};

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
  textFaint: '#A1A1AA',
  border: '#E4E4E7',
  borderFaint: '#F4F4F5',
  surface: '#FAFAFA',
  iconBg: '#F4F4F5',
};

function cleanLLM(text: string): string {
  return text
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/`(.+?)`/g, '$1');
}

/* ─── 상태 점 (모노크롬 + done/error만 tone) ─── */
function StatusDot({ status }: { status: Status }) {
  const colorMap = {
    idle: '#D4D4D8',
    streaming: '#0A0A0B',
    done: '#10B981',
    error: '#EF4444',
  };
  return <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: colorMap[status] }} />;
}

/* ─── 진행 dot (다크 배경용) ─── */
function DarkDot({ status }: { status: Status }) {
  const colorMap = {
    idle: 'rgba(255,255,255,0.25)',
    streaming: '#FFFFFF',
    done: '#10B981',
    error: '#EF4444',
  };
  return <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: colorMap[status] }} />;
}

/* ─── 히어로 종합 카드 (다크) ─── */
function SynthHero({
  status, text, statuses,
}: {
  status: Status;
  text: string;
  statuses: Record<AgentName, Status>;
}) {
  const D = DOMAIN.synth;
  return (
    <View style={{
      marginHorizontal: 16, marginTop: 14,
      borderRadius: 14, padding: 16,
      backgroundColor: NEUTRAL.ink,
    }}>
      {/* 헤더 */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <Ionicons name={D.icon} size={16} color="#FFFFFF" />
        <Text style={{ fontSize: 12, fontWeight: '700', color: '#FFFFFF', letterSpacing: 0.3, flex: 1 }}>
          {D.title}
        </Text>
        <Text style={{ fontSize: 10, fontWeight: '700', color: 'rgba(255,255,255,0.7)' }}>
          {status === 'done' ? '완료' : status === 'streaming' ? '생성 중' : status === 'error' ? '실패' : '대기'}
        </Text>
      </View>
      {/* 본문: synth LLM 텍스트 — 다크 배경 마크다운 렌더, 카드 높이 고정 내부 스크롤 */}
      <ScrollView
        style={{ maxHeight: 220 }}
        showsVerticalScrollIndicator={false}
        nestedScrollEnabled
      >
        {text ? (
          <Markdown
            style={{
              body: { fontSize: 14, color: '#F4F4F5', lineHeight: 22, fontWeight: '500' },
              heading1: { fontSize: 16, fontWeight: '800', color: '#FFFFFF', marginTop: 4, marginBottom: 6 },
              heading2: { fontSize: 15, fontWeight: '800', color: '#FFFFFF', marginTop: 8, marginBottom: 4 },
              heading3: { fontSize: 13, fontWeight: '700', color: '#FFFFFF', letterSpacing: 0.3, marginTop: 8, marginBottom: 4 },
              strong: { fontWeight: '800', color: '#FFFFFF' },
              em: { fontStyle: 'italic', color: '#F4F4F5' },
              bullet_list: { marginVertical: 4 },
              ordered_list: { marginVertical: 4 },
              list_item: { marginVertical: 2, fontSize: 14, color: '#F4F4F5', lineHeight: 22 },
              hr: { backgroundColor: 'rgba(255,255,255,0.15)', height: 1, marginVertical: 8 },
              paragraph: { marginVertical: 4 },
            }}>
            {text}
          </Markdown>
        ) : (
          <Text style={{ fontSize: 14, color: '#F4F4F5', lineHeight: 22, fontWeight: '500', minHeight: 60 }}>
            {status === 'idle'
              ? '아래 카드를 눌러 도메인별 상세 분석을 확인하세요.\n4개 도메인 분석이 완료되면 종합 결론이 표시됩니다.'
              : 'AI가 4개 도메인 분석을 종합하고 있습니다.\n잠시만 기다려 주세요.'}
          </Text>
        )}
        {status === 'streaming' && (
          <Text style={{ fontSize: 14, color: '#FFFFFF' }}> ▎</Text>
        )}
      </ScrollView>
      {/* 진행 dots */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12, paddingTop: 10,
        borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.12)' }}>
        {(['risk', 'sise', 'locale', 'support'] as AgentName[]).map((a) => (
          <View key={a} style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <DarkDot status={statuses[a]} />
            <Text style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)' }}>{DOMAIN[a].title}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

/* ─── 도메인 점수 추출 헬퍼 ─── */
function getDomainSummary(
  agent: AgentName,
  scores: ScoresPayload | null,
  preferredCategory?: string | null,
): { primary: string; sub: string; tone?: 'safe' | 'warn' | 'danger' } {
  if (!scores) return { primary: '–', sub: '대기' };

  if (agent === 'risk') {
    const r = scores.risk;
    if (!r) return { primary: '–', sub: '대기' };
    const tone = r.grade === '안전' ? 'safe' : r.grade === '주의' ? 'warn' : 'danger';
    return {
      primary: r.grade ?? '–',
      sub: r.risk_pct != null ? `위험도 ${r.risk_pct}%` : '–',
      tone,
    };
  }
  if (agent === 'sise') {
    const s = (scores.sise ?? {}) as Record<string, unknown>;
    const v = s.verdict as string | undefined;
    const ratio = s.ratio as number | undefined;
    // 적정 = 중립(평가 없음), 저렴 = safe, 비쌈 = danger
    const tone: 'safe' | 'danger' | undefined =
      v === '비쌈' ? 'danger' : v === '저렴' ? 'safe' : undefined;
    return {
      primary: v ?? '–',
      sub: ratio != null ? `적정가 ${Math.round(ratio * 100)}%` : '–',
      tone,
    };
  }
  if (agent === 'locale') {
    const l = (scores.locale ?? {}) as Record<string, unknown>;
    const counts = (l.counts ?? {}) as Record<string, number>;
    // 사용자 선호 카테고리 우선 표시 (개인화)
    if (preferredCategory && counts[preferredCategory] != null) {
      const label = CATEGORY_LABELS[preferredCategory] ?? preferredCategory;
      const areaName = l.area_name as string | undefined;
      return {
        primary: `${label} ${counts[preferredCategory]}`,
        sub: areaName ? `${areaName} · 내 관심` : '내 관심 카테고리',
      };
    }
    // 폴백: 편의 + 의료
    const conv = l.convenience as number | undefined;
    const med = l.medical as number | undefined;
    return {
      primary: conv != null ? `편의 ${conv}` : '–',
      sub: med != null ? `의료 ${med}` : '–',
    };
  }
  if (agent === 'support') {
    const sp = (scores.support ?? {}) as Record<string, unknown>;
    const count = sp.count as number | undefined;
    const monthly = sp.max_monthly as number | undefined;
    return {
      primary: count != null ? `${count}건` : '–',
      sub: monthly != null ? `최대 월 ${monthly}만` : '–',
    };
  }
  return { primary: '–', sub: '' };
}

/* ─── 미니 도메인 타일 (모노크롬 + tone은 평가에만) ─── */
function MiniTile({
  agent, scores, status, onPress, preferredCategory,
}: {
  agent: AgentName;
  scores: ScoresPayload | null;
  status: Status;
  onPress: () => void;
  preferredCategory?: string | null;
}) {
  const D = DOMAIN[agent];
  const { primary, sub, tone } = getDomainSummary(agent, scores, preferredCategory);
  const toneColor = tone === 'danger' ? '#B91C1C' : tone === 'safe' ? '#047857' : tone === 'warn' ? '#B45309' : NEUTRAL.ink;

  return (
    <Pressable
      onPress={onPress}
      style={{
        flex: 1,
        backgroundColor: 'white',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: NEUTRAL.border,
        padding: 12,
      }}>
      {/* 헤더 row — 도메인 구분은 아이콘+이름, 색은 중립 */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 }}>
        <View style={{ width: 24, height: 24, borderRadius: 6, backgroundColor: NEUTRAL.iconBg,
          alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name={D.icon} size={12} color={NEUTRAL.ink2} />
        </View>
        <Text style={{ fontSize: 11, fontWeight: '700', color: NEUTRAL.textMute, flex: 1 }}>
          {D.title}
        </Text>
        <StatusDot status={status} />
        <Ionicons name="chevron-forward" size={12} color={NEUTRAL.textFaint} />
      </View>
      {/* 핵심 점수 — tone은 평가가 있을 때만 */}
      <Text style={{ fontSize: 18, fontWeight: '800', color: toneColor, letterSpacing: -0.3 }}>
        {primary}
      </Text>
      <Text style={{ fontSize: 11, color: NEUTRAL.textMute, marginTop: 2 }}>
        {sub}
      </Text>
    </Pressable>
  );
}

/* ─── 메인 export — 5 도메인 패널 ─── */
export interface DomainPanelProps {
  scores: ScoresPayload | null;
  statuses: Record<AgentName, Status>;
  agentTexts: Record<AgentName, string>;
  onDomainPress: (agent: Exclude<AgentName, 'synth'>) => void;
}

export function DomainPanel({ scores, statuses, agentTexts, onDomainPress }: DomainPanelProps) {
  // 사용자 lifestyle_tag → 인프라 카테고리 (locale 미니 타일 개인화)
  const lifestyleTags = useDiagnosisStore((s) => s.lifestyleTags);
  const preferredCategory = useMemo(() => {
    for (const t of lifestyleTags) {
      const cat = TAG_TO_CATEGORY[t.name];
      if (cat) return cat;
    }
    return null;
  }, [lifestyleTags]);

  return (
    <View>
      <SynthHero status={statuses.synth} text={agentTexts.synth} statuses={statuses} />
      {/* 2x2 그리드 */}
      <View style={{ marginHorizontal: 16, marginTop: 10, gap: 8 }}>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <MiniTile agent="risk"   scores={scores} status={statuses.risk}   onPress={() => onDomainPress('risk')} />
          <MiniTile agent="sise"   scores={scores} status={statuses.sise}   onPress={() => onDomainPress('sise')} />
        </View>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <MiniTile agent="locale"  scores={scores} status={statuses.locale}  onPress={() => onDomainPress('locale')}
                    preferredCategory={preferredCategory} />
          <MiniTile agent="support" scores={scores} status={statuses.support} onPress={() => onDomainPress('support')} />
        </View>
      </View>
    </View>
  );
}
