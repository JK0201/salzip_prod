import client from './client';
import type { CardKey } from './policies';

export type EligiblePolicy = {
  id: string;
  name: string;
  card_key: CardKey | null;
  support_type: string | null;
  monthly_amount_wan: number | null;
  loan_limit: number | null;
  duration_months: number | null;
  agency_name: string | null;
  apply_url: string | null;
  age_min: number | null;
  age_max: number | null;
  is_homeless_required: boolean | null;
  income_max_annual: number | null;
  rent_limit: number | null;
  deposit_limit: number | null;
};

export type UserCriteria = {
  age: number;
  annual_income_wan: number;
  home_ownerless: boolean;
  deposit_max_wan: number;
  monthly_rent_max_wan: number;
};

export type EligibleResult = {
  policies: EligiblePolicy[];
  criteria: UserCriteria | null;
};

export async function fetchEligiblePolicies(): Promise<EligibleResult> {
  const { data } = await client.get<EligibleResult>('/api/v1/policies/eligible');
  console.log('[api] eligible policies count:', data.policies?.length);
  return data;
}
