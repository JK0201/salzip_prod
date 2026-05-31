import type {
  UserProfile,
  ProfileStats,
  ActiveApplication,
  SavedListing,
  DiagnoseInfo,
} from '@/types/profile';

// TODO: TanStack Query로 교체 예정 (서버 연동 시)

export const MOCK_PROFILE: UserProfile = {
  name: '박지원',
  joinedAt: '2026-04-15',
  age: 27,
  job: '백엔드',
};

export const MOCK_STATS: ProfileStats = {
  savedListings: 5,
  savedNeighborhoods: 3,
  activeApplications: 1,
};

export const MOCK_DIAGNOSE: DiagnoseInfo = {
  lastDiagnoseDaysAgo: 15,
};

export const MOCK_ACTIVE_APPLICATION: ActiveApplication = {
  id: 'app-1',
  programName: '청년월세 한시 특별지원',
  programIcon: '💰',
  currentStep: 1,
  totalSteps: 3,
  nextTask: '서류 준비 — 정부24 방문',
  daysLeft: 3,
  status: '진행 중',
};

export const MOCK_SAVED_LISTINGS: SavedListing[] = [
  {
    id: 'l-1',
    type: '빌라',
    unit: '302호',
    neighborhood: '성수동2가',
    deposit: 2800,
    monthly: 58,
    area: 15,
    commuteMin: 32,
    floor: 2,
    riskPercent: 8,
    riskLevel: 'safe',
    hugAvailable: true,
  },
  {
    id: 'l-2',
    type: '오피스텔',
    unit: '905호',
    neighborhood: '금호동',
    deposit: 3000,
    monthly: 60,
    area: 12,
    commuteMin: 28,
    floor: 9,
    riskPercent: 15,
    riskLevel: 'safe',
    hugAvailable: true,
  },
  {
    id: 'l-3',
    type: '다세대',
    unit: '201호',
    neighborhood: '화양동',
    deposit: 3000,
    monthly: 55,
    area: 14,
    commuteMin: 38,
    floor: 1,
    riskPercent: 42,
    riskLevel: 'warn',
    hugAvailable: true,
  },
];
