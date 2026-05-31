import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';

interface Props {
  title: string;
  onAction?: () => void;
  actionIcon?: ComponentProps<typeof Ionicons>['name'];
}

export function AppHeader({ title, onAction, actionIcon = 'options-outline' }: Props) {
  return (
    <View className="flex-row items-center justify-between px-4 h-10 border-b border-[#F4F4F5]">
      <Text className="text-[12px] font-bold text-[#0A0A0B] tracking-[-0.12px]">{title}</Text>
      {onAction ? (
        <Pressable onPress={onAction} className="w-7 h-7 items-center justify-center active:opacity-50">
          <Ionicons name={actionIcon} size={18} color="#18181B" />
        </Pressable>
      ) : (
        <View className="w-7" />
      )}
    </View>
  );
}
