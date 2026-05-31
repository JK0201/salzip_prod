// 도메인 디테일 시트 — 1개 도메인의 점수 디테일 + LLM 풀 텍스트 스트리밍
import { View, Text, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Markdown from 'react-native-markdown-display';
import type { AgentName, ScoresPayload } from '@/api/analyze';
import type { Status } from './DomainCards';

// 컬러 정책: 도메인 구분은 아이콘+라벨, 색은 모노크롬. tone은 평가 영역에만.
const DOMAIN_META: Record<
  Exclude<AgentName, 'synth'>,
  { title: string; sub: string; icon: keyof typeof Ionicons.glyphMap }
> = {
  risk:    { title: '위험 분석',  sub: '깡통전세·전세사기 진단',     icon: 'shield-checkmark-outline' },
  sise:    { title: '시세 분석',  sub: '주변 실거래 대비 적정성',    icon: 'pricetag-outline' },
  locale:  { title: '입지 분석',  sub: '교통·생활 인프라',           icon: 'location-outline' },
  support: { title: '지원사업',   sub: '신청 가능 청년 지원금',      icon: 'cash-outline' },
};

const NEUTRAL = {
  ink: '#0A0A0B',
  ink2: '#18181B',
  text: '#27272A',
  textMute: '#71717A',
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

function StatusText({ status }: { status: Status }) {
  // 모노크롬 + done/error만 tone
  const map = {
    idle:      { text: '대기',     color: NEUTRAL.textMute },
    streaming: { text: '생성 중',  color: NEUTRAL.ink },
    done:      { text: '완료',     color: '#047857' },
    error:     { text: '실패',     color: '#B91C1C' },
  };
  const s = map[status];
  return (
    <Text style={{ fontSize: 11, fontWeight: '700', color: s.color }}>{s.text}</Text>
  );
}

/* ─── 점수 디테일 ─── */
const TREND_LABELS: Record<string, string> = {
  unsold: '미분양',
  apt_tx_monthly: '아파트 거래량',
  apt_conv_ratio: '전월세전환율',
  apt_sale_tx_monthly: '아파트 매매 거래',
  housing_tx_monthly: '주택 거래량',
};

function trendToKorean(trend: Record<string, unknown> | undefined): string | null {
  if (!trend) return null;
  // 백엔드 summary가 "미분양 증가·거래량 감소 → 역전세 주의" 한글이면 그대로
  const summary = trend.summary as string | undefined;
  if (summary && !/[a-z_]+:/.test(summary)) return summary;
  // 영어 fallback이면 한글 라벨로 재조립
  const parts: string[] = [];
  for (const [key, val] of Object.entries(trend)) {
    if (key === 'summary') continue;
    const v = val as { direction?: string } | undefined;
    const label = TREND_LABELS[key] ?? key;
    if (v?.direction) parts.push(`${label} ${v.direction}`);
  }
  return parts.length > 0 ? parts.join(' · ') : null;
}

function RiskScoreBlock({ data }: { data: ScoresPayload['risk'] }) {
  if (!data) return <Text style={{ fontSize: 12, color: '#A1A1AA' }}>점수 대기 중</Text>;
  const tone = data.grade === '위험' ? '#B91C1C' : data.grade === '주의' ? '#B45309' : '#047857';
  const summary = trendToKorean(data.market_trend as Record<string, unknown> | undefined);
  return (
    <View style={{ gap: 10 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <View style={{ width: 64, height: 64, borderRadius: 32, borderWidth: 5, borderColor: tone,
          backgroundColor: 'white', alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 17, fontWeight: '800', color: tone }}>
            {data.risk_pct != null ? `${data.risk_pct}%` : '–'}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 11, color: '#71717A', marginBottom: 2 }}>종합 위험도</Text>
          <Text style={{ fontSize: 18, fontWeight: '800', color: tone }}>{data.grade ?? '–'}</Text>
        </View>
      </View>
      {data.factors && data.factors.length > 0 && (
        <View>
          <Text style={{ fontSize: 10, fontWeight: '700', color: '#0A0A0B', marginBottom: 6 }}>산출 4축</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            {data.factors.map((f) => (
              <View key={f.name} style={{ flex: 1, minWidth: '47%', backgroundColor: '#FAFAFA',
                borderRadius: 8, padding: 10 }}>
                <Text style={{ fontSize: 10, color: '#71717A' }}>{f.name}</Text>
                <Text style={{ fontSize: 15, fontWeight: '800', color: '#0A0A0B', marginTop: 2 }}>
                  {f.score}점
                </Text>
                <Text style={{ fontSize: 9, color: '#A1A1AA', marginTop: 1 }}>
                  가중 {Math.round(f.weight * 100)}%
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}
      {summary && (
        <View style={{ backgroundColor: '#FAFAFA', borderRadius: 8, padding: 10 }}>
          <Text style={{ fontSize: 10, color: '#71717A', marginBottom: 2 }}>시장 추세</Text>
          <Text style={{ fontSize: 12, fontWeight: '600', color: '#0A0A0B' }}>{summary}</Text>
        </View>
      )}
    </View>
  );
}

function SiseScoreBlock({ data }: { data: ScoresPayload['sise'] }) {
  const d = (data ?? {}) as Record<string, unknown>;
  const verdict = d.verdict as string | undefined;
  const ratio = d.ratio as number | undefined;
  const median = d.median_conv as number | undefined;
  const sample = d.sample_size as number | undefined;
  // 적정 = 중립(평가 없음), 저렴 = safe, 비쌈 = danger
  const tone = verdict === '비쌈' ? '#B91C1C' : verdict === '저렴' ? '#047857' : NEUTRAL.ink;
  return (
    <View style={{ gap: 10 }}>
      <View style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
        <View style={{ backgroundColor: '#FAFAFA', borderRadius: 12, padding: 14, alignItems: 'center', minWidth: 80 }}>
          <Text style={{ fontSize: 22, fontWeight: '800', color: tone, letterSpacing: -0.5 }}>
            {verdict ?? '–'}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 11, color: '#71717A' }}>적정가 대비</Text>
          <Text style={{ fontSize: 18, fontWeight: '800', color: '#0A0A0B' }}>
            {ratio != null ? `${Math.round(ratio * 100)}%` : '–'}
          </Text>
        </View>
      </View>
      <View style={{ backgroundColor: '#FAFAFA', borderRadius: 8, padding: 10 }}>
        <Text style={{ fontSize: 11, color: '#3F3F46' }}>
          동네·평형 중위 {median != null ? median.toLocaleString() : '–'} · 표본 {sample ?? '–'}건
        </Text>
      </View>
    </View>
  );
}

function LocaleScoreBlock({ data }: { data: ScoresPayload['locale'] }) {
  const d = (data ?? {}) as Record<string, unknown>;
  const counts = (d.counts ?? {}) as Record<string, number>;
  const labels: { key: keyof typeof counts; label: string }[] = [
    { key: 'cafe',     label: '카페' },
    { key: 'food',     label: '음식점' },
    { key: 'culture',  label: '문화' },
    { key: 'park',     label: '공원' },
    { key: 'mart',     label: '마트' },
    { key: 'subway',   label: '지하철' },
    { key: 'hospital', label: '병원' },
    { key: 'pharmacy', label: '약국' },
  ];
  return (
    <View>
      <Text style={{ fontSize: 10, fontWeight: '700', color: '#0A0A0B', marginBottom: 6 }}>
        인프라 8종 ({d.area_name ?? '–'})
      </Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
        {labels.map(({ key, label }) => (
          <View key={key} style={{ width: '23%', backgroundColor: '#FAFAFA',
            borderRadius: 8, padding: 8, alignItems: 'center' }}>
            <Text style={{ fontSize: 13, fontWeight: '800', color: '#0A0A0B' }}>{counts[key] ?? '–'}</Text>
            <Text style={{ fontSize: 9, color: '#71717A', marginTop: 1 }}>{label}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function SupportScoreBlock({ data }: { data: ScoresPayload['support'] }) {
  const d = (data ?? {}) as Record<string, unknown>;
  const count = d.count as number | undefined;
  const monthly = d.max_monthly as number | undefined;
  const loan = d.max_loan as number | undefined;
  const programs = (d.programs ?? []) as Array<{ name?: string; support_type?: string }>;
  return (
    <View style={{ gap: 10 }}>
      <View style={{ flexDirection: 'row', gap: 8 }}>
        <View style={{ flex: 1, backgroundColor: NEUTRAL.surface, borderRadius: 8, padding: 10 }}>
          <Text style={{ fontSize: 11, color: NEUTRAL.textMute }}>신청 가능</Text>
          <Text style={{ fontSize: 17, fontWeight: '800', color: NEUTRAL.ink, marginTop: 2 }}>{count ?? '–'}건</Text>
        </View>
        <View style={{ flex: 1, backgroundColor: '#FAFAFA', borderRadius: 8, padding: 10 }}>
          <Text style={{ fontSize: 11, color: '#71717A' }}>최대 월</Text>
          <Text style={{ fontSize: 14, fontWeight: '800', color: '#0A0A0B', marginTop: 2 }}>
            {monthly != null ? `${monthly.toLocaleString()}만` : '–'}
          </Text>
        </View>
        <View style={{ flex: 1, backgroundColor: '#FAFAFA', borderRadius: 8, padding: 10 }}>
          <Text style={{ fontSize: 11, color: '#71717A' }}>최대 대출</Text>
          <Text style={{ fontSize: 14, fontWeight: '800', color: '#0A0A0B', marginTop: 2 }}>
            {loan != null ? `${loan.toLocaleString()}만` : '–'}
          </Text>
        </View>
      </View>
      {programs.length > 0 && (
        <View>
          <Text style={{ fontSize: 10, fontWeight: '700', color: '#0A0A0B', marginBottom: 6 }}>대표 프로그램</Text>
          {programs.slice(0, 3).map((p, i) => (
            <View key={i} style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <Ionicons name="checkmark-circle" size={12} color="#10B981" />
              <Text style={{ fontSize: 11, color: '#3F3F46', flex: 1 }}>
                {p.name ?? '–'} <Text style={{ color: '#71717A' }}>· {p.support_type ?? '–'}</Text>
              </Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function ScoreBlock({ domain, scores }: { domain: Exclude<AgentName, 'synth'>; scores: ScoresPayload | null }) {
  if (domain === 'risk')    return <RiskScoreBlock data={scores?.risk ?? null} />;
  if (domain === 'sise')    return <SiseScoreBlock data={scores?.sise ?? null} />;
  if (domain === 'locale')  return <LocaleScoreBlock data={scores?.locale ?? null} />;
  if (domain === 'support') return <SupportScoreBlock data={scores?.support ?? null} />;
  return null;
}

/* ─── 메인 시트 ─── */
export interface DomainDetailSheetProps {
  visible: boolean;
  domain: Exclude<AgentName, 'synth'> | null;
  scores: ScoresPayload | null;
  status: Status;
  text: string;
  onClose: () => void;
}

export function DomainDetailSheet({ visible, domain, scores, status, text, onClose }: DomainDetailSheetProps) {
  if (!visible || !domain) return null;
  const M = DOMAIN_META[domain];

  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 20 }}>
      <Pressable style={{ flex: 1, backgroundColor: 'rgba(10,10,11,0.5)' }} onPress={onClose} />
      <View style={{
        position: 'absolute', top: 60, left: 0, right: 0, bottom: 0,
        backgroundColor: '#FAFAFA',
        borderTopLeftRadius: 20, borderTopRightRadius: 20,
      }}>
        {/* 핸들 */}
        <View style={{ alignItems: 'center', paddingTop: 8, paddingBottom: 4 }}>
          <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: '#D4D4D8' }} />
        </View>
        {/* 헤더 */}
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, paddingVertical: 12 }}>
          <View style={{ width: 40, height: 40, borderRadius: 10, backgroundColor: NEUTRAL.iconBg,
            alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name={M.icon} size={20} color={NEUTRAL.ink2} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: NEUTRAL.ink }}>{M.title}</Text>
            <Text style={{ fontSize: 11, color: NEUTRAL.textMute, marginTop: 2 }}>{M.sub}</Text>
          </View>
          <StatusText status={status} />
          <Pressable onPress={onClose}
            style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center', marginLeft: 4 }}>
            <Ionicons name="close" size={22} color={NEUTRAL.ink} />
          </Pressable>
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 32 }}>
          {/* 점수 디테일 */}
          <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14, marginBottom: 12 }}>
            <Text style={{ fontSize: 10, fontWeight: '700', color: '#71717A', letterSpacing: 0.5, marginBottom: 10 }}>
              결정론 점수
            </Text>
            <ScoreBlock domain={domain} scores={scores} />
          </View>
          {/* LLM 자연어 해석 */}
          <View style={{ backgroundColor: 'white', borderRadius: 12, padding: 14 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 }}>
              <Ionicons name="sparkles" size={12} color={NEUTRAL.ink2} />
              <Text style={{ fontSize: 10, fontWeight: '700', color: NEUTRAL.textMute, letterSpacing: 0.5 }}>
                AI 자연어 해석
              </Text>
            </View>
            {text ? (
              <Markdown
                style={{
                  body: { fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
                  heading1: { fontSize: 16, fontWeight: '800', color: NEUTRAL.ink, marginTop: 4, marginBottom: 6 },
                  heading2: { fontSize: 14, fontWeight: '800', color: NEUTRAL.ink, marginTop: 8, marginBottom: 4 },
                  heading3: { fontSize: 13, fontWeight: '700', color: NEUTRAL.ink, marginTop: 6, marginBottom: 3 },
                  strong: { fontWeight: '800', color: NEUTRAL.ink },
                  em: { fontStyle: 'italic', color: NEUTRAL.text },
                  bullet_list: { marginVertical: 4 },
                  ordered_list: { marginVertical: 4 },
                  list_item: { marginVertical: 2, fontSize: 13, color: NEUTRAL.text, lineHeight: 21 },
                  table: { borderWidth: 1, borderColor: NEUTRAL.border, borderRadius: 6, marginVertical: 8 },
                  thead: { backgroundColor: NEUTRAL.surface },
                  th: { padding: 8, fontWeight: '700', fontSize: 12, color: NEUTRAL.ink, borderRightWidth: 1, borderColor: NEUTRAL.border },
                  td: { padding: 8, fontSize: 12, color: NEUTRAL.text, borderTopWidth: 1, borderRightWidth: 1, borderColor: NEUTRAL.border },
                  hr: { backgroundColor: NEUTRAL.borderFaint, height: 1, marginVertical: 8 },
                  paragraph: { marginVertical: 4 },
                  blockquote: { backgroundColor: NEUTRAL.surface, borderLeftWidth: 3, borderLeftColor: NEUTRAL.ink, paddingHorizontal: 10, paddingVertical: 6, marginVertical: 6 },
                  code_inline: { backgroundColor: NEUTRAL.surface, paddingHorizontal: 4, borderRadius: 4, fontSize: 12 },
                }}>
                {text}
              </Markdown>
            ) : (
              <Text style={{ fontSize: 13, color: NEUTRAL.text, lineHeight: 21 }}>분석 대기 중...</Text>
            )}
            {status === 'streaming' && (
              <Text style={{ fontSize: 13, color: NEUTRAL.ink, marginTop: 2 }}> ▎</Text>
            )}
          </View>
        </ScrollView>
      </View>
    </View>
  );
}
