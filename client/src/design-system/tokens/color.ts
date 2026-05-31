export const color = {
  primary: {
    normal: '#0A0A0B',
  },
  brand: {
    normal: '#10B981',
    soft: '#ECFDF5',
  },
  label: {
    normal: '#18181B',
    alternative: '#71717A',
    assistive: '#A1A1AA',
  },
  line: {
    normal: '#E4E4E7',
  },
  background: {
    base: '#FFFFFF',
    soft: '#FAFAFA',
    elevated: '#F0F0F3',
    selected: '#E0E1E6',
  },
  status: {
    cautionary: '#F59E0B',
    negative: '#EF4444',
  },
} as const;

export type Color = typeof color;
