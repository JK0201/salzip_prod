export type Listing = {
  id: string;
  kind: string;
  estimated_kind: string | null;
  building_name: string | null;
  deposit: number;
  monthly_rent: number;
  area_m2: number | null;
  floor: number | null;
  lat: number;
  lng: number;
  flood_risk: boolean | null;
  build_year: number | null;
  jibun: string | null;
};

export type AreaMetrics = {
  cafe_count: number;
  food_count: number;
  culture_count: number;
  park_count: number;
  mart_count: number;
  subway_count: number;
  hospital_count: number;
  pharmacy_count: number;
};

export type AreaSafety = {
  avg_jeonse_ratio: number | null;
  flood_ratio: number | null;
  avg_build_year: number | null;
};

export type AreaScores = {
  work: number;
  life: number;
  safe: number;
};

export type Area = {
  area_id: string;
  rank: number;
  name: string;
  meta: string;
  score: number;
  tier: 1 | 2 | 3;
  lat: number;
  lng: number;
  commuteMinutes: number;
  scores: AreaScores;
  listing_count: number;
  flood_risk_count: number;
  reason: string;
  listings: Listing[];
  metrics: AreaMetrics;
  safety: AreaSafety;
};

export type RecommendResult = {
  areas: Area[];
  match_id: string | null;
  created_at?: string | null;
  request?: { age?: number; job_type?: string; [k: string]: unknown } | null;
};
