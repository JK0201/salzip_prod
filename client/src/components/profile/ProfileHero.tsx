import { View, Text, Pressable } from 'react-native';
import type { UserProfile, ProfileStats } from '@/types/profile';

type Props = {
  profile: UserProfile;
  stats: ProfileStats;
  onPressEdit: () => void;
};

export function ProfileHero({ profile, stats, onPressEdit }: Props) {
  const initial = profile.name.charAt(0);
  const joinedYear = profile.joinedAt.slice(0, 7).replace('-', '.');

  return (
    <View className="mx-5 mb-4 rounded-3xl bg-neutral-900 p-6">
      <View className="flex-row items-center">
        <View className="h-14 w-14 items-center justify-center rounded-full bg-emerald-600">
          <Text className="text-2xl font-extrabold text-white">{initial}</Text>
        </View>

        <View className="ml-4 flex-1">
          <Text className="text-lg font-extrabold text-white">{profile.name}</Text>
          <Text className="mt-1 text-xs text-white/60">
            {joinedYear} 가입 · {profile.age}세 · {profile.job}
          </Text>
        </View>

        <Pressable
          onPress={onPressEdit}
          className="rounded-full border border-white/15 bg-white/10 px-3 py-2"
        >
          <Text className="text-xs font-semibold text-white">프로필 편집</Text>
        </Pressable>
      </View>

      <View className="my-5 h-px bg-white/10" />

      <View className="flex-row">
        <StatCell num={stats.savedListings} unit="건" label="저장 매물" />
        <StatCell num={stats.savedNeighborhoods} unit="곳" label="저장 동네" />
        <StatCell num={stats.activeApplications} unit="건" label="진행 중 신청" />
      </View>
    </View>
  );
}

function StatCell({ num, unit, label }: { num: number; unit: string; label: string }) {
  return (
    <View className="flex-1">
      <View className="flex-row items-baseline">
        <Text className="text-2xl font-extrabold text-white">{num}</Text>
        <Text className="ml-0.5 text-sm font-semibold text-white/80">{unit}</Text>
      </View>
      <Text className="mt-1.5 text-xs text-white/60">{label}</Text>
    </View>
  );
}
