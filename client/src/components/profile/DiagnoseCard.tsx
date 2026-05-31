import { View, Text, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

type Props = {
  daysAgo: number;
  onPress: () => void;
};

export function DiagnoseCard({ daysAgo, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      className="mx-5 mb-4 flex-row items-center rounded-2xl border border-neutral-200 bg-white p-4"
    >
      <View className="h-11 w-11 items-center justify-center rounded-xl bg-emerald-50">
        <Ionicons name="refresh" size={20} color="#047857" />
      </View>

      <View className="ml-3 flex-1">
        <Text className="text-sm font-bold text-neutral-900">재진단하기</Text>
        <Text className="mt-0.5 text-xs text-neutral-400">
          조건이 바뀌었거나, 새 동네 추천을 받고 싶다면
        </Text>
      </View>

      <View className="ml-2 rounded-full bg-amber-100 px-2.5 py-1">
        <Text className="text-[11px] font-bold text-amber-800">
          {daysAgo === 0 ? '오늘 진단' : `${daysAgo}일 전 진단`}
        </Text>
      </View>

      <Ionicons name="chevron-forward" size={18} color="#8A8A92" className="ml-1" />
    </Pressable>
  );
}
