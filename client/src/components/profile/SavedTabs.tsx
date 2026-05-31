import { View, Text, Pressable } from 'react-native';

export type SavedTabKey = 'listing' | 'neighborhood';

type Props = {
  active: SavedTabKey;
  listingCount: number;
  neighborhoodCount: number;
  onChange: (key: SavedTabKey) => void;
};

export function SavedTabs({ active, listingCount, neighborhoodCount, onChange }: Props) {
  return (
    <View className="mb-3.5 flex-row gap-2">
      <TabButton
        active={active === 'listing'}
        label="매물"
        count={listingCount}
        onPress={() => onChange('listing')}
      />
      <TabButton
        active={active === 'neighborhood'}
        label="동네"
        count={neighborhoodCount}
        onPress={() => onChange('neighborhood')}
      />
    </View>
  );
}

function TabButton({
  active,
  label,
  count,
  onPress,
}: {
  active: boolean;
  label: string;
  count: number;
  onPress: () => void;
}) {
  const containerCls = active
    ? 'rounded-full border bg-neutral-900 border-neutral-900 px-4 py-2'
    : 'rounded-full border bg-neutral-50 border-neutral-200 px-4 py-2';
  const labelCls = active
    ? 'text-sm font-semibold text-white'
    : 'text-sm font-semibold text-neutral-500';
  const countCls = active ? 'ml-1 text-[11px] text-white/70' : 'ml-1 text-[11px] text-neutral-400';

  return (
    <Pressable onPress={onPress} className={containerCls}>
      <View className="flex-row items-baseline">
        <Text className={labelCls}>{label}</Text>
        <Text className={countCls}>{count}</Text>
      </View>
    </Pressable>
  );
}
