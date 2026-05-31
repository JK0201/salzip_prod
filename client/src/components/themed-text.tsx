import { Platform, Text, type TextProps } from 'react-native';

import { useDS } from '@/design-system';
import { type TypographyKey } from '@/design-system/tokens/typography';
import { Fonts } from '@/constants/theme';

type TextType = 'default' | 'title' | 'small' | 'smallBold' | 'subtitle' | 'link' | 'linkPrimary' | 'code';
type TextColor = 'text' | 'textSecondary';

export type ThemedTextProps = TextProps & {
  type?: TextType;
  themeColor?: TextColor;
};

const typeToTypographyKey: Record<TextType, TypographyKey> = {
  default:     'body/1',
  small:       'label/1',
  smallBold:   'label/1',
  title:       'display/2',
  subtitle:    'title/1',
  link:        'label/1',
  linkPrimary: 'label/1',
  code:        'caption/1',
};

export function ThemedText({ style, type = 'default', themeColor, ...rest }: ThemedTextProps) {
  const ds = useDS();

  const color = themeColor === 'textSecondary'
    ? ds.color.label.alternative
    : ds.color.label.normal;

  const typo = ds.typography[typeToTypographyKey[type]];

  const typeOverride =
    type === 'linkPrimary' ? { color: ds.color.brand.normal } :
    type === 'smallBold'   ? { fontWeight: '700' as const } :
    type === 'code'        ? { fontFamily: Fonts.mono, fontWeight: Platform.select({ android: '700' as const }) ?? ('500' as const) } :
    undefined;

  return (
    <Text
      style={[{ color }, typo, typeOverride, style]}
      {...rest}
    />
  );
}
