import { create } from 'zustand';

import type { LifestyleTag } from '@/api/lifestyleTags';
import type { Area } from '@/types/recommend';

export const COMMUTE_OPTIONS = ['30분 이내', '45분 이내', '1시간 이내'] as const;
export const HOUSEHOLD_TYPES = ['1인 가구', '청년 부부', '예비 신혼', '한부모'] as const;

type CommuteOption = (typeof COMMUTE_OPTIONS)[number];
type HouseholdType = (typeof HOUSEHOLD_TYPES)[number];

interface DiagnosisState {
  // step1
  companyName: string;
  workAddress: string;
  jobCategoryId: string;
  jobCategoryName: string;
  // step2
  commuteLimit: CommuteOption;
  lifestyleTags: LifestyleTag[];
  // step3
  depositWan: number;
  monthlyRentWan: number;
  // step4
  age: string;
  annualIncomeWan: string;
  householdType: HouseholdType;
  homeOwnerless: boolean;
  // 진단 결과
  results: Area[];
  matchId: string | null;
  resultView: 'map' | 'list';

  setCompanyName: (v: string) => void;
  setWorkAddress: (v: string) => void;
  setJobCategory: (id: string, name: string) => void;
  setCommuteLimit: (v: CommuteOption) => void;
  toggleLifestyle: (tag: LifestyleTag) => void;
  setDepositWan: (v: number) => void;
  setMonthlyRentWan: (v: number) => void;
  setAge: (v: string) => void;
  setAnnualIncomeWan: (v: string) => void;
  setHouseholdType: (v: HouseholdType) => void;
  setHomeOwnerless: (v: boolean) => void;
  setResults: (areas: Area[], matchId?: string | null) => void;
  setResultView: (v: 'map' | 'list') => void;
}

export const useDiagnosisStore = create<DiagnosisState>((set) => ({
  companyName: '',
  workAddress: '',
  jobCategoryId: '',
  jobCategoryName: '',
  commuteLimit: '45분 이내',
  lifestyleTags: [],
  depositWan: 3000,
  monthlyRentWan: 60,
  age: '',
  annualIncomeWan: '',
  householdType: '1인 가구',
  homeOwnerless: true,
  results: [],
  matchId: null,
  resultView: 'map',

  setCompanyName: (v) => set({ companyName: v }),
  setWorkAddress: (v) => set({ workAddress: v }),
  setJobCategory: (id, name) => set({ jobCategoryId: id, jobCategoryName: name }),
  setCommuteLimit: (v) => set({ commuteLimit: v }),
  toggleLifestyle: (tag) =>
    set((s) => ({
      lifestyleTags: s.lifestyleTags.some((t) => t.id === tag.id)
        ? s.lifestyleTags.filter((t) => t.id !== tag.id)
        : [...s.lifestyleTags, tag],
    })),
  setDepositWan: (v) => set({ depositWan: v }),
  setMonthlyRentWan: (v) => set({ monthlyRentWan: v }),
  setAge: (v) => set({ age: v }),
  setAnnualIncomeWan: (v) => set({ annualIncomeWan: v }),
  setHouseholdType: (v) => set({ householdType: v }),
  setHomeOwnerless: (v) => set({ homeOwnerless: v }),
  setResults: (areas, matchId = null) => set({ results: areas, matchId }),
  setResultView: (v) => set({ resultView: v }),
}));
