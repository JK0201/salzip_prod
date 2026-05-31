import client from './client';

export type FavoriteItem = {
  listing_id: string;
  kind: string;
  estimated_kind: string | null;
  building_name: string | null;
  deposit: number;
  monthly_rent: number;
  area_m2: number | null;
  floor: number | null;
  flood_risk: boolean | null;
  build_year: number | null;
  umd_name: string | null;
  lat: number | null;
  lng: number | null;
  risk_level: string;
  created_at: string;
};

export type FavoritesResponse = {
  items: FavoriteItem[];
  ids: string[];
};

export async function getFavorites(): Promise<FavoritesResponse> {
  const { data } = await client.get<FavoritesResponse>('/api/v1/favorites');
  return data;
}

export async function addFavorite(listingId: string): Promise<void> {
  await client.post(`/api/v1/favorites/${listingId}`);
}

export async function removeFavorite(listingId: string): Promise<void> {
  await client.delete(`/api/v1/favorites/${listingId}`);
}
