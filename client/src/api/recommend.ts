import client from './client';
import type { RecommendResult } from '@/types/recommend';

export type RecommendRequest = {
  workplace_name: string;
  workplace_address: string;
  job_type: string;
  max_commute_minutes: number;
  lifestyle_tags: string[];
  deposit_max_wan: number;
  monthly_rent_max_wan: number;
  age: number;
  annual_income_wan: number;
  household_type: string;
  home_ownerless: boolean;
};

export async function postRecommend(body: RecommendRequest): Promise<RecommendResult> {
  console.log('[api] postRecommend body', body);
  const { data } = await client.post<RecommendResult>('/api/v1/recommend', body);
  console.log('[api] postRecommend response areas:', data.areas?.length, 'match_id:', data.match_id);
  return data;
}

// 세션 기반 최근 추천 복원 (새로고침/재진입 대비)
export async function getLatestRecommend(): Promise<RecommendResult> {
  const { data } = await client.get<RecommendResult>('/api/v1/recommend/latest');
  console.log('[api] getLatestRecommend areas:', data.areas?.length, 'match_id:', data.match_id);
  return data;
}
