import client from './client';

export type FloodStatus = {
  address: string;
  lat: number;
  lng: number;
  flooded: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  lastUpdatedAt: string;
};

export async function fetchFloodStatus(params: {
  lat: number;
  lng: number;
}): Promise<FloodStatus> {
  const { data } = await client.get<FloodStatus>('/api/v1/flood', { params });
  return data;
}
