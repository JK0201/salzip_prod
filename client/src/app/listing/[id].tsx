// Route: /listing/[id] (S06: 매물 상세 + S06-1 위험도 모달)
import { useState, useEffect, useMemo, useRef } from 'react';
import { View, Text, Pressable, ScrollView, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { listingDetailImages } from '@/constants/listingImages';
import { useFavoriteStore } from '@/store/useFavoriteStore';
import { useDiagnosisStore } from '@/store/useDiagnosisStore';
import { getLatestRecommend } from '@/api/recommend';
import type { Area, Listing } from '@/types/recommend';
import { Ionicons } from '@expo/vector-icons';
import { startAnalyze, type AgentName, type ScoresPayload } from '@/api/analyze';
import { DomainPanel, type Status } from '@/components/listing/DomainCards';
import { DomainDetailSheet } from '@/components/listing/DomainDetailSheet';
import { SaljipChatModal } from '@/components/listing/SaljipChatModal';
import { ExtraActions } from '@/components/listing/ExtraActions';

/* ─── 타입 & 색상 시스템 ─── */
type RiskLevel = 'safe' | 'warn' | 'danger';

const RISK = {
  safe:   { bg: '#ECFDF5', border: '#D1FAE5', ring: '#10B981', accent: '#047857', label: '안전 등급', tag: '안전' },
  warn:   { bg: '#FFFBEB', border: '#FEF3C7', ring: '#F59E0B', accent: '#B45309', label: '주의 등급', tag: '주의' },
  danger: { bg: '#FEF2F2', border: '#FEE2E2', ring: '#EF4444', accent: '#B91C1C', label: '위험 등급', tag: '위험' },
};

const CTA = {
  safe:   { bg: '#0A0A0B', text: '살집이에게 물어보세요', icon: 'chatbubbles-outline' as const },
  warn:   { bg: '#B45309', text: '주의 매물 — 살집이에게 물어보세요', icon: 'chatbubbles-outline' as const },
  danger: { bg: '#B91C1C', text: '위험 매물 — 살집이에게 물어보세요', icon: 'chatbubbles-outline' as const },
};

/* ─── 데이터 ─── */
type EvidenceItem = { label: string; value: string; badge: string; level: RiskLevel; icon: keyof typeof Ionicons.glyphMap };
type FactorCard   = { name: string; weight: string; data: string; source: string; score: number; level: RiskLevel };
type MetaTag      = { text: string; highlighted?: boolean; level?: RiskLevel };

type Detail = {
  title: string;
  priceLabel: string;
  area: string; kind: string;
  riskPct: number; riskLevel: RiskLevel;
  riskDesc: string;
  metaTags: MetaTag[];
  evidence: EvidenceItem[];
  factors: FactorCard[];
};

const DETAILS: Record<string, Detail> = {
  '1': {
    title: '성수동 빌라 · 2층', priceLabel: '보증 3,000만 / 월 60만',
    area: '33㎡ (10평)', kind: '원룸',
    riskPct: 12, riskLevel: 'safe',
    riskDesc: '전세가율 65% · 침수이력 0건 · HUG 가능',
    metaTags: [{ text: '33㎡ (10평)' }, { text: '원룸' }, { text: '2025년 리모델링' }],
    evidence: [
      { label: '전세가율',   value: '65%',    badge: '안전', level: 'safe',   icon: 'cash-outline' },
      { label: '유형 사고율', value: '2.1%',   badge: '안전', level: 'safe',   icon: 'shield-outline' },
      { label: '침수 이력',  value: '없음',    badge: '0건',  level: 'safe',   icon: 'water-outline' },
      { label: 'HUG 보증',  value: '가입 가능', badge: '가능', level: 'safe',   icon: 'checkmark-circle-outline' },
    ],
    factors: [
      { name: '전세가율',    weight: '가중 40%', data: '매매 4,600만 대비 전세 3,000만 = 65%', source: '국토부 실거래가 (최근 6개월)', score: 100, level: 'safe' },
      { name: '유형 사고율', weight: '가중 20%', data: '빌라·다세대 전세사기 사고율 2.1% (성동구 평균)', source: 'HUG 보증사고 통계', score: 90, level: 'safe' },
      { name: '침수 이력',   weight: '가중 20%', data: '최근 10년 침수 흔적 0건 · 침수예상 구역 해당 없음', source: '행안부 침수흔적도 + 침수예상도', score: 100, level: 'safe' },
      { name: 'HUG 보증 가입', weight: '가중 20%', data: '전세가율 90% 이하 + 주택 유형 충족 → 가입 가능', source: 'HUG 전세보증금 반환보증 기준', score: 80, level: 'safe' },
    ],
  },
  '3': {
    title: '신림동 다세대 · 반지하', priceLabel: '전세 8,000만',
    area: '43㎡ (13평)', kind: '투룸',
    riskPct: 45, riskLevel: 'warn',
    riskDesc: '전세가율 82% · 침수이력 1건 · HUG 조건부',
    metaTags: [{ text: '43㎡ (13평)' }, { text: '투룸' }, { text: '반지하', highlighted: true, level: 'warn' }],
    evidence: [
      { label: '전세가율',   value: '82%',    badge: '주의',  level: 'warn',   icon: 'cash-outline' },
      { label: '유형 사고율', value: '8.4%',   badge: '주의',  level: 'warn',   icon: 'shield-outline' },
      { label: '침수 이력',  value: '2022년',  badge: '1건',   level: 'warn',   icon: 'water-outline' },
      { label: 'HUG 보증',  value: '심사 필요', badge: '조건부', level: 'warn',   icon: 'alert-circle-outline' },
    ],
    factors: [
      { name: '전세가율',    weight: '가중 40%', data: '매매 9,800만 대비 전세 8,000만 = 82%', source: '국토부 실거래가 (최근 6개월)', score: 45, level: 'warn' },
      { name: '유형 사고율', weight: '가중 20%', data: '다세대 전세사기 사고율 8.4% (관악구 평균)', source: 'HUG 보증사고 통계', score: 55, level: 'warn' },
      { name: '침수 이력',   weight: '가중 20%', data: '최근 10년 침수 흔적 1건 · 2022년 기록', source: '행안부 침수흔적도', score: 50, level: 'warn' },
      { name: 'HUG 보증 가입', weight: '가중 20%', data: '전세가율 90% 미만이나 반지하로 심사 필요', source: 'HUG 전세보증금 반환보증 기준', score: 55, level: 'warn' },
    ],
  },
  '4': {
    title: '봉천동 원룸 · 1층', priceLabel: '전세 12,000만',
    area: '26㎡ (8평)', kind: '원룸',
    riskPct: 78, riskLevel: 'danger',
    riskDesc: '전세가율 95% · 사고율 12% · 침수 3건',
    metaTags: [{ text: '26㎡ (8평)' }, { text: '원룸' }, { text: '⚠ 고위험', highlighted: true, level: 'danger' }],
    evidence: [
      { label: '전세가율',   value: '95%',    badge: '위험', level: 'danger', icon: 'cash-outline' },
      { label: '유형 사고율', value: '12.3%',  badge: '위험', level: 'danger', icon: 'shield-outline' },
      { label: '침수 이력',  value: '2020·22·23', badge: '3건', level: 'danger', icon: 'water-outline' },
      { label: 'HUG 보증',  value: '가입 불가',  badge: '불가', level: 'danger', icon: 'close-circle-outline' },
    ],
    factors: [
      { name: '전세가율',    weight: '가중 40%', data: '매매 1.26억 대비 전세 1.2억 = 95%', source: '국토부 실거래가 (최근 6개월)', score: 5, level: 'danger' },
      { name: '유형 사고율', weight: '가중 20%', data: '원룸·고시원 전세사기 사고율 12.3% (관악구)', source: 'HUG 보증사고 통계', score: 15, level: 'danger' },
      { name: '침수 이력',   weight: '가중 20%', data: '최근 10년 침수 흔적 3건 · 2020·22·23년', source: '행안부 침수흔적도 + 침수예상도', score: 10, level: 'danger' },
      { name: 'HUG 보증 가입', weight: '가중 20%', data: '전세가율 90% 초과 → 보증 가입 불가', source: 'HUG 전세보증금 반환보증 기준', score: 0, level: 'danger' },
    ],
  },
};

const DEFAULT_ID = '1';

/* ─── 서브 컴포넌트 ─── */

function RiskCircle({ pct, level, size = 52 }: { pct: number; level: RiskLevel; size?: number }) {
  const r = RISK[level];
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2,
      borderWidth: size * 0.1, borderColor: r.ring,
      backgroundColor: 'white', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <Text style={{ fontSize: size * 0.26, fontWeight: '800', color: r.accent, letterSpacing: -0.5 }}>
        {pct}%
      </Text>
    </View>
  );
}

function EvidenceGrid({ items }: { items: EvidenceItem[] }) {
  return (
    <View style={{ marginHorizontal: 16, marginTop: 14 }}>
      <Text style={{ fontSize: 12, fontWeight: '700', color: '#0A0A0B', marginBottom: 8 }}>산출 근거 4종</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
        {items.map((item) => {
          const r = RISK[item.level];
          return (
            <View key={item.label} style={{ width: '47.5%', backgroundColor: '#FAFAFA',
              borderWidth: 1, borderColor: '#F4F4F5', borderRadius: 10, padding: 10, gap: 4 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <View style={{ width: 24, height: 24, borderRadius: 6, backgroundColor: r.bg,
                  alignItems: 'center', justifyContent: 'center' }}>
                  <Ionicons name={item.icon} size={13} color={r.accent} />
                </View>
                <View style={{ backgroundColor: r.bg, paddingHorizontal: 5, paddingVertical: 2, borderRadius: 4 }}>
                  <Text style={{ fontSize: 9, fontWeight: '700', color: r.accent }}>{item.badge}</Text>
                </View>
              </View>
              <Text style={{ fontSize: 10, color: '#71717A', fontWeight: '500' }}>{item.label}</Text>
              <Text style={{ fontSize: 15, fontWeight: '800', color: item.level === 'danger' ? r.accent : '#0A0A0B',
                letterSpacing: -0.3 }}>{item.value}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

/* ─── RiskModal (S06-1) ─── */
function RiskModal({ detail, onClose }: { detail: Detail; onClose: () => void }) {
  const r = RISK[detail.riskLevel];
  const gradeLegend = [
    { label: '0~30% 안전', bg: '#D1FAE5', text: '#047857' },
    { label: '31~60% 주의', bg: '#FEF3C7', text: '#B45309' },
    { label: '61%+ 위험', bg: '#FEE2E2', text: '#B91C1C' },
  ];

  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 20 }}>
      <Pressable style={{ flex: 1, backgroundColor: 'rgba(10,10,11,0.5)' }} onPress={onClose} />
      <View style={{ backgroundColor: 'white', borderTopLeftRadius: 20, borderTopRightRadius: 20,
        maxHeight: '85%', shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 20, elevation: 12 }}>
        {/* 핸들 */}
        <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: '#D4D4D8',
          alignSelf: 'center', marginTop: 10, marginBottom: 6 }} />

        <ScrollView showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 24 }}>
          {/* 히어로 */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 14,
            borderBottomWidth: 1, borderBottomColor: '#F4F4F5', marginBottom: 14 }}>
            <RiskCircle pct={detail.riskPct} level={detail.riskLevel} size={64} />
            <View style={{ flex: 1 }}>
              <Text style={{ fontSize: 18, fontWeight: '800', color: '#0A0A0B', letterSpacing: -0.36, marginBottom: 4 }}>
                깡통전세 위험도
              </Text>
              <View style={{ backgroundColor: r.bg, alignSelf: 'flex-start',
                paddingHorizontal: 7, paddingVertical: 2, borderRadius: 4, marginBottom: 4 }}>
                <Text style={{ fontSize: 10, fontWeight: '700', color: r.accent, letterSpacing: 0.4 }}>
                  {r.label}
                </Text>
              </View>
              <Text style={{ fontSize: 11, color: '#71717A' }}>{detail.title} · {detail.priceLabel}</Text>
            </View>
          </View>

          {/* 팩터 카드 4종 */}
          <Text style={{ fontSize: 11, fontWeight: '700', color: '#71717A', letterSpacing: 0.8,
            textTransform: 'uppercase', marginBottom: 10 }}>산출 근거 4종</Text>
          <View style={{ gap: 6 }}>
            {detail.factors.map((f) => {
              const fr = RISK[f.level];
              const leftBorderColor = { safe: '#10B981', warn: '#F59E0B', danger: '#EF4444' }[f.level];
              return (
                <View key={f.name} style={{ borderWidth: 1, borderColor: '#E4E4E7', borderRadius: 10,
                  borderLeftWidth: 3, borderLeftColor: leftBorderColor,
                  paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                  <View style={{ flex: 1 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                      <Text style={{ fontSize: 12, fontWeight: '700', color: '#0A0A0B' }}>{f.name}</Text>
                      <Text style={{ fontSize: 9, color: '#71717A', fontFamily: 'Courier' }}>{f.weight}</Text>
                    </View>
                    <Text style={{ fontSize: 11, color: '#71717A', lineHeight: 16 }}>{f.data}</Text>
                    <Text style={{ fontSize: 8, color: '#A1A1AA', marginTop: 2 }}>출처: {f.source}</Text>
                  </View>
                  <Text style={{ fontSize: 16, fontWeight: '800', color: fr.accent, minWidth: 36, textAlign: 'right' }}>
                    {f.score}
                  </Text>
                </View>
              );
            })}
          </View>

          {/* 등급 범례 */}
          <View style={{ flexDirection: 'row', borderRadius: 8, overflow: 'hidden', marginTop: 14 }}>
            {gradeLegend.map(({ label, bg, text }) => (
              <View key={label} style={{ flex: 1, backgroundColor: bg, padding: 6, alignItems: 'center' }}>
                <Text style={{ fontSize: 9, fontWeight: '700', color: text }}>{label}</Text>
              </View>
            ))}
          </View>
          <Text style={{ fontSize: 10, fontWeight: '700', color: r.accent, marginTop: 4, paddingLeft: 4 }}>
            ▲ 현재 {detail.riskPct}%
          </Text>

          {/* 알고리즘 링크 */}
          <View style={{ alignItems: 'center', marginTop: 14 }}>
            <Text style={{ fontSize: 12, fontWeight: '600', color: '#047857',
              borderBottomWidth: 1, borderBottomColor: '#A7F3D0', paddingBottom: 1 }}>
              이 알고리즘은 어떻게 계산되나요? →
            </Text>
          </View>
        </ScrollView>
      </View>
    </View>
  );
}

/* ─── Main Screen ─── */
/* ─── store 매물 → Detail 일부 필드 빌드 (가격/면적/제목/태그만, risk는 mock 유지) ─── */
function findListing(areas: Area[], lid: string | undefined): { listing: Listing; area: Area } | null {
  if (!lid) return null;
  for (const a of areas) {
    const l = a.listings.find((x) => x.id === lid);
    if (l) return { listing: l, area: a };
  }
  return null;
}

function buildRealOverrides(match: { listing: Listing; area: Area } | null): Partial<Detail> {
  if (!match) return {};
  const { listing: l, area } = match;
  const kindStr = l.estimated_kind ?? l.kind ?? '';
  const floorStr = l.floor != null ? ` · ${l.floor}층` : '';
  const priceLabel =
    l.monthly_rent > 0
      ? `보증 ${l.deposit.toLocaleString()}만 / 월 ${l.monthly_rent}만`
      : `전세 ${l.deposit.toLocaleString()}만`;
  const areaStr = l.area_m2
    ? `${l.area_m2.toFixed(1)}㎡ (${Math.round(l.area_m2 / 3.3058)}평)`
    : '';
  const tags: MetaTag[] = [];
  if (areaStr) tags.push({ text: areaStr });
  if (kindStr) tags.push({ text: kindStr });
  if (l.build_year) tags.push({ text: `${l.build_year}년 건축` });
  return {
    title: `${area.name}${l.building_name ? ` ${l.building_name}` : ''}${floorStr}`,
    priceLabel,
    area: areaStr,
    kind: kindStr,
    metaTags: tags,
  };
}

/* ─── 백엔드 risk 결정론 점수 → Detail 필드 변환 ─── */
function gradeToLevel(grade: '안전' | '주의' | '위험' | undefined): RiskLevel | null {
  if (grade === '안전') return 'safe';
  if (grade === '주의') return 'warn';
  if (grade === '위험') return 'danger';
  return null;
}

function scoreToLevel(score: number): RiskLevel {
  return score >= 80 ? 'safe' : score >= 50 ? 'warn' : 'danger';
}

function badgeText(score: number): string {
  return score >= 80 ? '안전' : score >= 50 ? '주의' : '위험';
}

function iconFor(name: string): keyof typeof Ionicons.glyphMap {
  if (name.includes('전세')) return 'cash-outline';
  if (name.includes('사고')) return 'shield-outline';
  if (name.includes('침수')) return 'water-outline';
  if (name.includes('HUG')) return 'checkmark-circle-outline';
  return 'information-circle-outline';
}

function fmtValue(name: string, basis: string | undefined, score: number): string {
  if (basis && name.includes('전세가율')) {
    const m = basis.match(/jeonse_ratio=([\d.]+)/);
    if (m) return `${parseFloat(m[1]).toFixed(0)}%`;
  }
  if (basis && name.includes('사고')) {
    const m = basis.match(/hug_accident_count=(\d+)/);
    if (m) return `${parseInt(m[1], 10).toLocaleString()}건`;
  }
  if (basis && name.includes('침수')) {
    const m = basis.match(/flood_risk=(\w+)/);
    if (m) return m[1] === 'True' ? '있음' : '없음';
  }
  if (name.includes('HUG')) return score >= 80 ? '가입 가능' : '조건부';
  return `${score}점`;
}

function buildRiskOverrides(scores: ScoresPayload | null): Partial<Detail> {
  const risk = scores?.risk;
  if (!risk || !risk.factors) return {};
  const level = gradeToLevel(risk.grade) ?? scoreToLevel(risk.total_safe ?? 100);

  const evidence: EvidenceItem[] = risk.factors.map((f) => ({
    label: f.name,
    value: fmtValue(f.name, f.basis, f.score),
    badge: badgeText(f.score),
    level: scoreToLevel(f.score),
    icon: iconFor(f.name),
  }));

  const factors: FactorCard[] = risk.factors.map((f) => ({
    name: f.name,
    weight: `가중 ${Math.round(f.weight * 100)}%`,
    data: f.basis ?? '',
    source: '결정론 점수 산출 근거',
    score: f.score,
    level: scoreToLevel(f.score),
  }));

  const descParts: string[] = [];
  for (const f of risk.factors) {
    if (f.name.includes('전세가율')) descParts.push(`전세가율 ${fmtValue(f.name, f.basis, f.score)}`);
    else if (f.name.includes('침수')) descParts.push(`침수 ${fmtValue(f.name, f.basis, f.score)}`);
    else if (f.name.includes('HUG')) descParts.push(`HUG ${fmtValue(f.name, f.basis, f.score)}`);
  }

  return {
    riskPct: risk.risk_pct,
    riskLevel: level,
    riskDesc: descParts.join(' · '),
    evidence,
    factors,
  };
}

export default function ListingDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const results = useDiagnosisStore((s) => s.results);
  const realMatch = useMemo(() => findListing(results, id), [results, id]);
  const baseDetail = DETAILS[id ?? DEFAULT_ID] ?? DETAILS[DEFAULT_ID];

  // 백엔드 SSE scores 이벤트 페이로드 (null이면 mock fallback)
  const [scores, setScores] = useState<ScoresPayload | null>(null);
  const riskOverrides = useMemo(() => buildRiskOverrides(scores), [scores]);

  const detail = useMemo(
    () => ({ ...baseDetail, ...buildRealOverrides(realMatch), ...riskOverrides }),
    [baseDetail, realMatch, riskOverrides],
  );
  const cta = CTA[detail.riskLevel];

  const saved = useFavoriteStore((s) => (id ? s.ids.has(id) : false));
  const toggleFav = useFavoriteStore((s) => s.toggle);

  // 5 도메인 SSE 상태 — 진입 시 자동 시작
  const [statuses, setStatuses] = useState<Record<AgentName, Status>>({
    risk: 'idle', sise: 'idle', locale: 'idle', support: 'idle', synth: 'idle',
  });
  const [agentTexts, setAgentTexts] = useState<Record<AgentName, string>>({
    risk: '', sise: '', locale: '', support: '', synth: '',
  });
  const [selectedDomain, setSelectedDomain] = useState<Exclude<AgentName, 'synth'> | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);

  // 새로고침 대응: lifestyleTags 휘발 시 latest에서 복원 (입지 미니 개인화용)
  useEffect(() => {
    if (useDiagnosisStore.getState().lifestyleTags.length > 0) return;
    getLatestRecommend()
      .then((res) => {
        const names = (res.request as { lifestyle_tags?: string[] } | undefined)?.lifestyle_tags;
        if (names && names.length > 0) {
          useDiagnosisStore.setState({
            lifestyleTags: names.map((n) => ({ id: n, name: n })),
          });
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!id) return;
    setScores(null);
    setStatuses({ risk: 'idle', sise: 'idle', locale: 'idle', support: 'idle', synth: 'idle' });
    setAgentTexts({ risk: '', sise: '', locale: '', support: '', synth: '' });
    stopRef.current = startAnalyze(id, {
      onScores: (s) => setScores(s),
      onAgentStart: (a) => setStatuses((p) => ({ ...p, [a]: 'streaming' })),
      onToken: (a, delta) => setAgentTexts((p) => ({ ...p, [a]: p[a] + delta })),
      onAgentDone: (a) => setStatuses((p) => ({ ...p, [a]: 'done' })),
      onAgentError: (a) => setStatuses((p) => ({ ...p, [a]: 'error' })),
    });
    return () => {
      if (stopRef.current) stopRef.current();
      stopRef.current = null;
    };
  }, [id]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#FFFFFF' }}>
      {/* 앱 바 */}
      <View style={{ height: 44, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <Pressable onPress={() => router.back()}
          style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name="chevron-back" size={22} color="#0A0A0B" />
        </Pressable>
        <Text style={{ fontSize: 13, fontWeight: '700', color: '#0A0A0B' }}>매물 상세</Text>
        <View style={{ flexDirection: 'row', gap: 0 }}>
          <Pressable style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="share-outline" size={20} color="#18181B" />
          </Pressable>
          <Pressable onPress={() => id && toggleFav(id)}
            style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name={saved ? 'heart' : 'heart-outline'} size={20} color={saved ? '#EF4444' : '#18181B'} />
          </Pressable>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
        {/* 사진 영역 */}
        <View style={{ height: 200, position: 'relative' }}>
          <Image
            source={listingDetailImages(id ?? DEFAULT_ID)[0]}
            style={{ width: '100%', height: 200 }}
            resizeMode="cover"
          />
          {/* 페이지 도트 */}
          <View style={{ position: 'absolute', bottom: 10, left: 0, right: 0, flexDirection: 'row', justifyContent: 'center', gap: 4 }}>
            {listingDetailImages(id ?? DEFAULT_ID).map((_, i) => (
              <View key={i} style={{ height: 5, borderRadius: 3,
                width: i === 0 ? 14 : 5,
                backgroundColor: i === 0 ? 'white' : 'rgba(255,255,255,0.5)' }} />
            ))}
          </View>
        </View>

        {/* 매물 정보 */}
        <View style={{ paddingHorizontal: 16, paddingTop: 14 }}>
          <Text style={{ fontSize: 16, fontWeight: '800', color: '#0A0A0B', letterSpacing: -0.32, marginBottom: 4 }}>
            {detail.title}
          </Text>
          <Text style={{ fontSize: 15, fontWeight: '700', color: '#18181B', marginBottom: 8 }}>
            {detail.priceLabel}
          </Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 5 }}>
            {detail.metaTags.map(({ text, highlighted, level }) => {
              const tagR = level ? RISK[level] : null;
              return (
                <View key={text} style={{
                  backgroundColor: tagR ? tagR.bg : '#FAFAFA',
                  borderWidth: 1,
                  borderColor: tagR ? tagR.border : '#F4F4F5',
                  paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 }}>
                  <Text style={{ fontSize: 10, fontWeight: highlighted ? '700' : '500',
                    color: tagR ? tagR.accent : '#3F3F46' }}>{text}</Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* 5 도메인 패널 — 종합 히어로 + 4 도메인 미니 그리드 */}
        <DomainPanel
          scores={scores}
          statuses={statuses}
          agentTexts={agentTexts}
          onDomainPress={(a) => setSelectedDomain(a)}
        />

        {/* 부가 기능 — 출퇴근 노선·메일 리포트 (LLM 무관 유틸) */}
        <ExtraActions
          originArea={realMatch?.area.name ?? detail.title.split(' ')[0]}
          destLabel={useDiagnosisStore.getState().companyName || '회사'}
          listingTitle={detail.title}
        />

        {/* 하단 여백 (CTA 높이만큼) */}
        <View style={{ height: 80 }} />
      </ScrollView>

      {/* 고정 CTA */}
      <View style={{ paddingHorizontal: 16, paddingTop: 10, paddingBottom: 16,
        borderTopWidth: 1, borderTopColor: '#F4F4F5', backgroundColor: 'white' }}>
        <Pressable
          onPress={() => setChatOpen(true)}
          style={({ pressed }) => ({
            backgroundColor: cta.bg, borderRadius: 12, paddingVertical: 14,
            flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
            opacity: pressed ? 0.85 : 1,
          })}>
          <Ionicons name={cta.icon} size={16} color="white" />
          <Text style={{ color: 'white', fontSize: 14, fontWeight: '700' }}>{cta.text}</Text>
        </Pressable>
      </View>

      {/* 도메인 디테일 시트 — 미니 타일 클릭 시 */}
      <DomainDetailSheet
        visible={selectedDomain != null}
        domain={selectedDomain}
        scores={scores}
        status={selectedDomain ? statuses[selectedDomain] : 'idle'}
        text={selectedDomain ? agentTexts[selectedDomain] : ''}
        onClose={() => setSelectedDomain(null)}
      />

      {/* 살집이 챗 모달 — fixed CTA 클릭 시 */}
      <SaljipChatModal
        visible={chatOpen}
        onClose={() => setChatOpen(false)}
        listingTitle={detail.title}
        ownerLabel="임대인 김 O O"
      />
    </SafeAreaView>
  );
}
