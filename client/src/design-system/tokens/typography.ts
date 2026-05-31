// letterSpacing converted from em to pt (em * fontSize)
export const typography = {
  'display/1': { fontSize: 56, lineHeight: 72, letterSpacing: -1.79, fontWeight: '700' as const },
  'display/2': { fontSize: 40, lineHeight: 52, letterSpacing: -1.13, fontWeight: '700' as const },
  'display/3': { fontSize: 36, lineHeight: 48, letterSpacing: -0.97, fontWeight: '700' as const },
  'title/1':   { fontSize: 32, lineHeight: 44, letterSpacing: -0.81, fontWeight: '700' as const },
  'title/2':   { fontSize: 28, lineHeight: 38, letterSpacing: -0.66, fontWeight: '700' as const },
  'title/3':   { fontSize: 24, lineHeight: 32, letterSpacing: -0.55, fontWeight: '700' as const },
  'heading/1': { fontSize: 22, lineHeight: 30, letterSpacing: -0.43, fontWeight: '600' as const },
  'heading/2': { fontSize: 20, lineHeight: 28, letterSpacing: -0.24, fontWeight: '600' as const },
  'headline/1':{ fontSize: 18, lineHeight: 26, letterSpacing: -0.04, fontWeight: '600' as const },
  'headline/2':{ fontSize: 17, lineHeight: 24, letterSpacing:  0,     fontWeight: '600' as const },
  'body/1':    { fontSize: 16, lineHeight: 24, letterSpacing:  0.09,  fontWeight: '400' as const },
  'body/2':    { fontSize: 15, lineHeight: 22, letterSpacing:  0.14,  fontWeight: '400' as const },
  'label/1':   { fontSize: 14, lineHeight: 20, letterSpacing:  0.20,  fontWeight: '500' as const },
  'label/2':   { fontSize: 13, lineHeight: 18, letterSpacing:  0.25,  fontWeight: '500' as const },
  'caption/1': { fontSize: 12, lineHeight: 16, letterSpacing:  0.30,  fontWeight: '400' as const },
  'caption/2': { fontSize: 11, lineHeight: 14, letterSpacing:  0.34,  fontWeight: '400' as const },
} as const;

export type TypographyKey = keyof typeof typography;
export type TypographyStyle = (typeof typography)[TypographyKey];
