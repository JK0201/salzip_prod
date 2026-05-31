import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export function SectionHeader({
  title,
  action,
  onPressAction,
}: {
  title: string;
  action?: string;
  onPressAction?: () => void;
}) {
  return (
    <View className="mb-3.5 flex-row items-end justify-between">
      <Text className="text-lg font-extrabold text-neutral-900">{title}</Text>
      {action && (
        <Pressable onPress={onPressAction} className="flex-row items-center">
          <Text className="text-[13px] font-semibold text-neutral-400">{action}</Text>
          <Ionicons name="chevron-forward" size={14} color="#8A8A92" />
        </Pressable>
      )}
    </View>
  );
}

type MenuItemProps = {
  iconName: keyof typeof Ionicons.glyphMap;
  title: string;
  desc?: string;
  onPress: () => void;
  isLast?: boolean;
};

export function MenuItem({ iconName, title, desc, onPress, isLast }: MenuItemProps) {
  const border = isLast ? '' : 'border-b border-neutral-100';
  return (
    <Pressable
      onPress={onPress}
      className={`flex-row items-center gap-3.5 px-4 py-4 ${border}`}
    >
      <View className="h-9 w-9 items-center justify-center rounded-xl bg-neutral-50">
        <Ionicons name={iconName} size={18} color="#525258" />
      </View>

      <View className="flex-1">
        <Text className="text-sm font-semibold text-neutral-900">{title}</Text>
        {desc && <Text className="mt-0.5 text-xs text-neutral-400">{desc}</Text>}
      </View>

      <Ionicons name="chevron-forward" size={18} color="#8A8A92" />
    </Pressable>
  );
}
