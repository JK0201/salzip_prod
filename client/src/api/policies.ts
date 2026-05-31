import client from './client';

export type CardKey = 'monthly' | 'jeonse' | 'hug' | 'other';

export type PolicyPreviewItem = {
  id: string;
  name: string;
  card_key: CardKey | null;
  support_type: string | null;
  monthly_amount_wan: number | null;
  loan_limit: number | null;
  duration_months: number | null;
  agency_name: string | null;
  apply_url: string | null;
};

export type PolicyPreviewSummary = {
  total_matched: number;
  max_monthly_support_wan: number | null;
  max_loan_limit_wan: number | null;
};

export type PolicyPreviewResponse = {
  by_card: Partial<Record<CardKey, PolicyPreviewItem[]>>;
  summary: PolicyPreviewSummary;
};

export async function fetchPoliciesPreview(params: {
  deposit_max_wan: number;
  monthly_rent_max_wan: number;
}): Promise<PolicyPreviewResponse> {
  const { data } = await client.get<PolicyPreviewResponse>('/api/v1/policies/preview', {
    params,
  });
  return data;
}
