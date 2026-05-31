import client from './client';

export type Policy = {
  id: string;
  title: string;
  category: string;
  description: string;
  maxDepositWan?: number;
  maxMonthlyRentWan?: number;
};

export async function fetchPolicies(): Promise<Policy[]> {
  const { data } = await client.get<Policy[]>('/api/v1/policies');
  return data;
}

export async function fetchPolicyById(id: string): Promise<Policy> {
  const { data } = await client.get<Policy>(`/api/v1/policies/${id}`);
  return data;
}
