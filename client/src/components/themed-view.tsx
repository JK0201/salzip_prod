import { View, type ViewProps } from 'react-native';

import { useDS } from '@/design-system';

type ViewColorKey = 'background' | 'backgroundElement' | 'backgroundSelected';

export type ThemedViewProps = ViewProps & {
  type?: ViewColorKey;
};

export function ThemedView({ style, type = 'background', ...otherProps }: ThemedViewProps) {
  const ds = useDS();

  const backgroundColor =
    type === 'backgroundElement' ? ds.color.background.elevated :
    type === 'backgroundSelected' ? ds.color.background.selected :
    ds.color.background.base;

  return <View style={[{ backgroundColor }, style]} {...otherProps} />;
}
