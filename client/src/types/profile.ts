export type UserProfile = {
  name: string;
  joinedAt: string; // ISO date (e.g. "2026-04-15")
  age: number;
  job: string;
};

export type ProfileStats = {
  savedListings: number;
  savedNeighborhoods: number;
  activeApplications: number;
};

export type RiskLevel = 'safe' | 'warn' | 'danger';

export type SavedListing = {
  id: string;
  type: '빌라' | '오피스텔' | '다세대' | '원룸' | '투룸';
  unit: string; // "302호"
  neighborhood: string;
  deposit: number; // 만원 단위
  monthly: number; // 만원 단위
  area: number; // 평
  commuteMin: number;
  floor: number;
  riskPercent: number;
  riskLevel: RiskLevel;
  hugAvailable: boolean;
};

export type ApplicationStatus = '진행 중' | '완료' | '대기';

export type ActiveApplication = {
  id: string;
  programName: string;
  programIcon: string; // emoji
  currentStep: number;
  totalSteps: number;
  nextTask: string;
  daysLeft: number;
  status: ApplicationStatus;
};

export type DiagnoseInfo = {
  lastDiagnoseDaysAgo: number;
};
