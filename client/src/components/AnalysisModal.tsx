// 매물 AI 상세 분석 모달 — SSE 5 에이전트 토큰 스트리밍
import { useEffect, useRef, useState } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { startAnalyze, type AgentName, type ScoresPayload } from '@/api/analyze';

const AGENT_ORDER: AgentName[] = ['risk', 'sise', 'locale', 'support', 'synth'];

const AGENT_LABELS: Record<
  AgentName,
  { title: string; sub: string; icon: keyof typeof Ionicons.glyphMap; accent: string; bg: string }
> = {
  risk:    { title: '위험 분석',  sub: '깡통전세·전세사기 진단',      icon: 'shield-checkmark-outline', accent: '#B91C1C', bg: '#FEF2F2' },
  sise:    { title: '시세 분석',  sub: '주변 실거래 대비 적정성',     icon: 'pricetag-outline',         accent: '#B45309', bg: '#FFFBEB' },
  locale:  { title: '입지 분석',  sub: '교통·생활 인프라',            icon: 'location-outline',         accent: '#1D4ED8', bg: '#EFF6FF' },
  support: { title: '지원사업',   sub: '신청 가능 청년 지원금',       icon: 'cash-outline',             accent: '#047857', bg: '#ECFDF5' },
  synth:   { title: '종합 결론',  sub: 'AI 통합 의사결정 가이드',     icon: 'sparkles',                 accent: '#0A0A0B', bg: '#F4F4F5' },
};

type Status = 'idle' | 'streaming' | 'done' | 'error';

function cleanLLM(text: string): string {
  return text
    .replace(/^#{1,6}\s+/gm, '')        // ###
    .replace(/\*\*(.+?)\*\*/g, '$1')    // **bold**
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '$1')  // *italic*
    .replace(/`(.+?)`/g, '$1');         // `code`
}

function StatusBadge({ status }: { status: Status }) {
  if (status === 'idle') return null;
  const map = {
    streaming: { text: '분석 중', color: '#1D4ED8', bg: '#EFF6FF' },
    done:      { text: '완료',    color: '#047857', bg: '#ECFDF5' },
    error:     { text: '실패',    color: '#71717A', bg: '#F4F4F5' },
  } as const;
  const s = map[status];
  return (
    <View style={{ backgroundColor: s.bg, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 }}>
      <Text style={{ fontSize: 9, fontWeight: '700', color: s.color }}>{s.text}</Text>
    </View>
  );
}

function AgentCard({ agent, status, text }: { agent: AgentName; status: Status; text: string }) {
  const L = AGENT_LABELS[agent];
  const isSynth = agent === 'synth';
  return (
    <View
      style={{
        marginHorizontal: 16,
        marginTop: 12,
        borderRadius: 12,
        borderWidth: isSynth ? 1.5 : 1,
        borderColor: isSynth ? L.accent : '#F4F4F5',
        backgroundColor: 'white',
        padding: 14,
      }}>
      {/* 헤더 */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <View style={{ width: 32, height: 32, borderRadius: 8, backgroundColor: L.bg, alignItems: 'center', justifyContent: 'center' }}>
          <Ionicons name={L.icon} size={16} color={L.accent} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 14, fontWeight: '800', color: '#0A0A0B' }}>{L.title}</Text>
          <Text style={{ fontSize: 11, color: '#71717A', marginTop: 1 }}>{L.sub}</Text>
        </View>
        <StatusBadge status={status} />
      </View>
      {/* 본문 */}
      {text ? (
        <Text style={{ fontSize: 13, color: '#27272A', lineHeight: 20 }}>
          {cleanLLM(text)}
          {status === 'streaming' && <Text style={{ color: L.accent }}> ▎</Text>}
        </Text>
      ) : (
        <Text style={{ fontSize: 12, color: '#A1A1AA', fontStyle: 'italic' }}>
          {status === 'streaming' ? '분석을 시작합니다...' : '대기 중'}
        </Text>
      )}
    </View>
  );
}

export interface AnalysisModalProps {
  visible: boolean;
  listingId: string | undefined;
  onClose: () => void;
  onScores?: (scores: ScoresPayload) => void;
}

export function AnalysisModal({ visible, listingId, onClose, onScores }: AnalysisModalProps) {
  const [texts, setTexts] = useState<Record<AgentName, string>>({
    risk: '', sise: '', locale: '', support: '', synth: '',
  });
  const [statuses, setStatuses] = useState<Record<AgentName, Status>>({
    risk: 'idle', sise: 'idle', locale: 'idle', support: 'idle', synth: 'idle',
  });
  const [globalError, setGlobalError] = useState<string>('');
  const stopRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!visible || !listingId) return;
    // 모달 열림 = SSE 시작. 상태 리셋.
    setTexts({ risk: '', sise: '', locale: '', support: '', synth: '' });
    setStatuses({ risk: 'idle', sise: 'idle', locale: 'idle', support: 'idle', synth: 'idle' });
    setGlobalError('');

    stopRef.current = startAnalyze(listingId, {
      onScores: (s) => { onScores?.(s); },
      onAgentStart: (a) => setStatuses((p) => ({ ...p, [a]: 'streaming' })),
      onToken: (a, delta) => setTexts((p) => ({ ...p, [a]: p[a] + delta })),
      onAgentDone: (a) => setStatuses((p) => ({ ...p, [a]: 'done' })),
      onAgentError: (a) => setStatuses((p) => ({ ...p, [a]: 'error' })),
      onError: (e) => setGlobalError(String(e)),
    });

    return () => {
      if (stopRef.current) stopRef.current();
      stopRef.current = null;
    };
  }, [visible, listingId, onScores]);

  if (!visible) return null;

  return (
    <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 10 }}>
      {/* 백드롭 */}
      <Pressable style={{ flex: 1, backgroundColor: 'rgba(10,10,11,0.5)' }} onPress={onClose} />
      {/* 시트 */}
      <View
        style={{
          position: 'absolute', top: 60, left: 0, right: 0, bottom: 0,
          backgroundColor: '#FAFAFA',
          borderTopLeftRadius: 20, borderTopRightRadius: 20,
        }}>
        {/* 핸들 */}
        <View style={{ alignItems: 'center', paddingTop: 8, paddingBottom: 4 }}>
          <View style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: '#D4D4D8' }} />
        </View>
        {/* 헤더 */}
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12 }}>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: '800', color: '#0A0A0B' }}>AI 상세 분석</Text>
            <Text style={{ fontSize: 11, color: '#71717A', marginTop: 2 }}>
              4개 전문 에이전트 + 종합 — 실시간 스트리밍
            </Text>
          </View>
          <Pressable onPress={onClose}
            style={{ width: 32, height: 32, alignItems: 'center', justifyContent: 'center' }}>
            <Ionicons name="close" size={22} color="#0A0A0B" />
          </Pressable>
        </View>
        {globalError ? (
          <View style={{ marginHorizontal: 16, marginTop: 4, padding: 8, backgroundColor: '#FEF2F2', borderRadius: 6 }}>
            <Text style={{ fontSize: 11, color: '#B91C1C' }}>연결 오류: {globalError}</Text>
          </View>
        ) : null}
        {/* 카드 5종 */}
        <ScrollView contentContainerStyle={{ paddingBottom: 24 }}>
          {AGENT_ORDER.map((a) => (
            <AgentCard key={a} agent={a} status={statuses[a]} text={texts[a]} />
          ))}
        </ScrollView>
      </View>
    </View>
  );
}
