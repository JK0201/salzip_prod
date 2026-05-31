import client from './client';

export type LifestyleTag = { id: string; name: string };

export async function fetchLifestyleTags(): Promise<LifestyleTag[]> {
  console.log('[api] fetchLifestyleTags request');
  const { data } = await client.get<LifestyleTag[]>('/api/v1/lifestyle_tags');
  console.log('[api] fetchLifestyleTags response', data);
  return data;
}
