import client from './client';

export type JobCategory = { id: string; name: string };

export async function fetchJobCategories(): Promise<JobCategory[]> {
  console.log('[api] fetchJobCategories request');
  const { data } = await client.get<JobCategory[]>('/api/v1/job_categories');
  console.log('[api] fetchJobCategories response', data);
  return data;
}
