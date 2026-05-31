// 매물 분석 SSE 구독. 백엔드: POST /api/v1/listings/{id}/analyze (text/event-stream)
// 이벤트: route / agent_start / token{agent,delta} / agent_done / agent_error / done
import EventSource from 'react-native-sse';
import { useSessionStore } from '@/store/useSessionStore';
import { API_BASE_URL as BASE_URL } from '@/constants/env';

export type AgentName = 'risk' | 'sise' | 'locale' | 'support' | 'synth';

export type RiskFactor = {
  name: string;
  weight: number;
  score: number;
  basis?: string;
};

export type RiskScore = {
  risk_pct: number;
  grade: '안전' | '주의' | '위험';
  factors: RiskFactor[];
  jeonse_score?: number;
  accident_score?: number;
  flood_score?: number;
  hug_score?: number;
  total_safe?: number;
  market_trend?: Record<string, unknown>;
};

export type ScoresPayload = {
  risk?: RiskScore | null;
  sise?: Record<string, unknown> | null;
  locale?: Record<string, unknown> | null;
  support?: Record<string, unknown> | null;
};

export interface AnalyzeHandlers {
  onRoute?: (agents: string[]) => void;
  onScores?: (scores: ScoresPayload) => void;
  onAgentStart?: (agent: AgentName) => void;
  onToken?: (agent: AgentName, delta: string) => void;
  onAgentDone?: (agent: AgentName) => void;
  onAgentError?: (agent: AgentName, error: string) => void;
  onDone?: () => void;
  onError?: (err: unknown) => void;
}

export function startAnalyze(listingId: string, handlers: AnalyzeHandlers) {
  const token = useSessionStore.getState().token;
  const url = `${BASE_URL}/api/v1/listings/${listingId}/analyze`;

  type AnalyzeEvent = 'route' | 'scores' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'done';
  const es = new EventSource<AnalyzeEvent>(url, {
    method: 'POST',
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
    body: '{}',
  });

  const parse = (raw: unknown) => {
    if (typeof raw !== 'string') return null;
    try { return JSON.parse(raw); } catch { return null; }
  };

  es.addEventListener('route', (e: any) => {
    const d = parse(e.data);
    if (d?.agents) handlers.onRoute?.(d.agents);
  });
  es.addEventListener('scores', (e: any) => {
    const d = parse(e.data);
    if (d) handlers.onScores?.(d as ScoresPayload);
  });
  es.addEventListener('agent_start', (e: any) => {
    const d = parse(e.data);
    if (d?.agent) handlers.onAgentStart?.(d.agent as AgentName);
  });
  es.addEventListener('token', (e: any) => {
    const d = parse(e.data);
    if (d?.agent && typeof d?.delta === 'string') {
      handlers.onToken?.(d.agent as AgentName, d.delta);
    }
  });
  es.addEventListener('agent_done', (e: any) => {
    const d = parse(e.data);
    if (d?.agent) handlers.onAgentDone?.(d.agent as AgentName);
  });
  es.addEventListener('agent_error', (e: any) => {
    const d = parse(e.data);
    if (d?.agent) handlers.onAgentError?.(d.agent as AgentName, d.error ?? '');
  });
  es.addEventListener('done', () => {
    handlers.onDone?.();
    es.close();
  });
  es.addEventListener('error', (e: any) => {
    handlers.onError?.(e);
  });

  return () => es.close();
}
