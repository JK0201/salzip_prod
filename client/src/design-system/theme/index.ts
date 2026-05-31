import { color, space, radius, typography, shadow } from '../tokens';

export const lightTheme = {
  color,
  space,
  radius,
  typography,
  shadow,
} as const;

// Dark theme은 Phase 2에서 추가
export type Theme = typeof lightTheme;
