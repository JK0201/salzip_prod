import client from './client';

export type Listing = {
  id: string;
  title: string;
  address: string;
  lat: number;
  lng: number;
  depositWan: number;
  monthlyRentWan: number;
  areaM2: number;
};

export async function fetchListings(params?: {
  lat?: number;
  lng?: number;
  radius?: number;
}): Promise<Listing[]> {
  const { data } = await client.get<Listing[]>('/api/v1/listings', { params });
  return data;
}

export async function fetchListingById(id: string): Promise<Listing> {
  const { data } = await client.get<Listing>(`/api/v1/listings/${id}`);
  return data;
}
